"""The complete flow the app is built for."""
import io
import sys
import types
from unittest.mock import MagicMock

ELLA = {"latitude": 6.87, "longitude": 81.05}


def test_family_numbers_in_safety_card(client, tourist):
    h = tourist()
    assert client.post("/api/family-contacts", json={"name": "Mum", "phone": "077 123 4567"}, headers=h).status_code == 400
    r = client.post("/api/family-contacts", json={"name": "Mum", "phone": "+49 151 9876 5432"}, headers=h)
    assert r.status_code == 201 and r.json["contact"]["phone"] == "+4915198765432"
    other = tourist("bob@example.com")
    assert client.get("/api/family-contacts", headers=other).json["contacts"] == []


def test_typed_sos_identifies_incident_and_returns_tips_contacts_and_whatsapp(client, tourist, police):
    h = tourist()
    client.post("/api/family-contacts", json={"name": "Mum", "phone": "+4915198765432"}, headers=h)
    r = client.post("/api/sos", json={"message": "A snake bit my friend near the waterfall, his leg is swelling", **ELLA}, headers=h)
    assert r.status_code == 201, r.json
    inc = r.json["incident"]
    assert inc["incident_type"] == "animal_attack"
    assert inc["station"]["name"] == "Ella Police"
    g = inc["guidance"]
    assert "snakebite" in g["tip"].lower()
    assert g["nearest_police"]["number"] == "0572228622"
    assert [x["number"] for x in g["hotlines"]] == ["1990", "119"]
    assert any(c["kind"] == "nearest_hospital" for c in g["nearby_contacts"])
    fam = inc["family_alerts"]["recipients"][0]
    assert fam["name"] == "Mum" and fam["whatsapp_link"].startswith("https://wa.me/4915198765432?text=")
    assert "Animal Attack" in inc["family_alerts"]["message"] and "maps.google.com" in inc["family_alerts"]["message"]

    # Ella officers see it; Colombo officers do not
    ella_h, _ = police("ella-police")
    col_h, _ = police("colombo-fort-police")
    assert [i["id"] for i in client.get("/api/police/incidents", headers=ella_h).json["incidents"]] == [inc["id"]]
    assert client.get("/api/police/incidents", headers=col_h).json["incidents"] == []
    assert client.get(f"/api/police/incidents/{inc['id']}", headers=col_h).status_code == 403
    detail = client.get(f"/api/police/incidents/{inc['id']}", headers=ella_h).json["incident"]
    assert detail["tourist"]["name"] == "Anna" and detail["message_english"].startswith("A snake")


def test_voice_sos_uses_transcript(client, tourist):
    h = tourist()
    data = {"latitude": "6.87", "longitude": "81.05", "language": "en",
            "voice_transcript": "someone stole my bag at the bus station",
            "voice": (io.BytesIO(b"fake-webm-audio"), "sos.webm")}
    r = client.post("/api/sos", data=data, headers=h, content_type="multipart/form-data")
    assert r.status_code == 201, r.json
    assert r.json["incident"]["incident_type"] == "theft"
    msgs = client.get(f"/api/incidents/{r.json['incident']['id']}/messages", headers=h).json["messages"]
    voice = [m for m in msgs if m["kind"] == "voice"][0]
    assert voice["media_url"] and voice["body_english"] == "someone stole my bag at the bus station"


def test_one_tap_sos_then_message_sets_the_type(client, tourist):
    h = tourist()
    first = client.post("/api/sos", json=ELLA, headers=h).json["incident"]
    assert first["incident_type"] == "other"
    r = client.post("/api/sos", json={"message": "my wife collapsed and is not breathing", **ELLA}, headers=h)
    assert r.status_code == 200 and r.json["created"] is False
    assert r.json["incident"]["id"] == first["id"] and r.json["incident"]["incident_type"] == "medical"


def test_live_location_route_until_tourist_turns_it_off(client, tourist, police):
    h = tourist()
    iid = client.post("/api/sos", json={"message": "a man is following me", **ELLA}, headers=h).json["incident"]["id"]
    for lat in (6.871, 6.873, 6.876):
        assert client.post(f"/api/sos/{iid}/location", json={"latitude": lat, "longitude": 81.05}, headers=h).status_code == 201
    ella_h, _ = police()
    col_h, _ = police("colombo-fort-police")
    assert len(client.get(f"/api/incidents/{iid}/pings", headers=ella_h).json["pings"]) == 4  # start + 3 = route
    assert client.get(f"/api/incidents/{iid}/pings", headers=col_h).status_code == 403

    assert client.post(f"/api/sos/{iid}/tracking", json={"active": False}, headers=tourist("eve@example.com")).status_code == 403
    assert client.post(f"/api/sos/{iid}/tracking", json={"active": False}, headers=h).json["tracking_active"] is False
    assert client.post(f"/api/sos/{iid}/location", json={"latitude": 6.9, "longitude": 81.0}, headers=h).status_code == 409
    inc = client.get(f"/api/police/incidents/{iid}", headers=ella_h).json["incident"]
    assert inc["tracking_active"] is False and inc["tracking_events"][-1] == {**inc["tracking_events"][-1], "active": False, "by": "tourist"}
    assert client.post(f"/api/sos/{iid}/tracking", json={"active": True}, headers=h).json["tracking_active"] is True
    assert client.post(f"/api/sos/{iid}/location", json={"latitude": 6.9, "longitude": 81.0}, headers=h).status_code == 201


def test_chat_text_image_voice_and_media_privacy(client, tourist, police):
    h = tourist()
    iid = client.post("/api/sos", json={"message": "my passport was stolen", **ELLA}, headers=h).json["incident"]["id"]
    ella_h, ella_token = police()
    assert client.post(f"/api/incidents/{iid}/messages", data={"kind": "text", "body": "We are coming"}, headers=ella_h).status_code == 201
    img = client.post(f"/api/incidents/{iid}/messages", headers=h, content_type="multipart/form-data",
                      data={"kind": "image", "file": (io.BytesIO(b"\x89PNG"), "thief.png")})
    assert img.status_code == 201
    url = img.json["message"]["media_url"]
    bad = client.post(f"/api/incidents/{iid}/messages", headers=h, content_type="multipart/form-data",
                      data={"kind": "image", "file": (io.BytesIO(b"x"), "virus.exe")})
    assert bad.status_code == 400
    assert client.get(f"{url}?token={ella_token}").status_code == 200
    _, col_token = police("colombo-fort-police")
    assert client.get(f"{url}?token={col_token}").status_code == 403
    assert client.get(url).status_code == 401
    assert client.get(f"/api/incidents/{iid}/messages", headers=police("colombo-fort-police")[0]).status_code == 403


def test_police_status_resolved_stops_tracking(client, tourist, police):
    h = tourist()
    iid = client.post("/api/sos", json={"message": "there is a fire in my hotel", **ELLA}, headers=h).json["incident"]["id"]
    ella_h, _ = police()
    assert client.post(f"/api/police/incidents/{iid}/status", json={"status": "resolved"}, headers=ella_h).status_code == 200
    assert client.get("/api/sos/current", headers=h).json["incident"] is None
    assert client.post(f"/api/sos/{iid}/location", json=ELLA, headers=h).status_code == 409


def test_whatsapp_sent_automatically_with_twilio(app, client, tourist, monkeypatch):
    app.config.update(WHATSAPP_MODE="twilio", TWILIO_ACCOUNT_SID="AC1", TWILIO_AUTH_TOKEN="t",
                      TWILIO_WHATSAPP_FROM="+14155238886")
    twilio_client = MagicMock()
    rest = types.ModuleType("twilio.rest")
    rest.Client = lambda *a: twilio_client
    monkeypatch.setitem(sys.modules, "twilio", types.ModuleType("twilio"))
    monkeypatch.setitem(sys.modules, "twilio.rest", rest)
    h = tourist()
    client.post("/api/family-contacts", json={"name": "Dad", "phone": "+491701112223"}, headers=h)
    r = client.post("/api/sos", json={"message": "a man punched me outside the bar", **ELLA}, headers=h)
    assert r.json["incident"]["family_alerts"]["delivered"] is True
    kw = twilio_client.messages.create.call_args.kwargs
    assert kw["to"] == "whatsapp:+491701112223" and kw["from_"] == "whatsapp:+14155238886"
    assert "Physical Assault" in kw["body"]


def test_officer_must_use_strong_new_password(client, police):
    h, _ = police()
    assert client.post("/api/auth/police/change-password", json={"current_password": "Start12345x", "new_password": "short"}, headers=h).status_code == 400
    assert client.post("/api/auth/police/change-password", json={"current_password": "Start12345x", "new_password": "NewStrong2026pw"}, headers=h).status_code == 200
