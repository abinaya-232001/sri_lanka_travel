"""Socket rooms: only the incident's tourist and its station receive chat and location."""
from app.extensions import socketio


def _events(c, name):
    return [e["args"][0] for e in c.get_received() if e["name"] == name]


def test_only_participants_get_live_events(app, client, tourist, police):
    h = tourist()
    iid = client.post("/api/sos", json={"message": "someone is following me", "latitude": 6.87, "longitude": 81.05},
                      headers=h).json["incident"]["id"]
    t_token = h["Authorization"].split()[1]
    _, ella_token = police()
    _, col_token = police("colombo-fort-police")
    other_token = tourist("mallory@example.com")["Authorization"].split()[1]

    sock = {n: socketio.test_client(app, query_string=f"token={tok}")
            for n, tok in (("tourist", t_token), ("ella", ella_token), ("colombo", col_token), ("other", other_token))}
    for s in sock.values():
        s.get_received()
        s.emit("join_incident", {"incident_id": iid})
    assert _events(sock["tourist"], "joined_incident") and _events(sock["ella"], "joined_incident")
    assert _events(sock["colombo"], "join_denied") and _events(sock["other"], "join_denied")

    client.post(f"/api/sos/{iid}/location", json={"latitude": 6.872, "longitude": 81.05}, headers=h)
    client.post(f"/api/incidents/{iid}/messages", data={"kind": "text", "body": "help"}, headers=h)
    assert _events(sock["ella"], "location:update")
    assert not _events(sock["colombo"], "location:update") and not _events(sock["other"], "chat:message")

    sock["ella"].emit("typing", {"incident_id": iid, "role": "tourist"})  # role is set by the server
    assert _events(sock["tourist"], "typing")[0]["role"] == "police"


def test_new_sos_alerts_only_the_nearest_station(app, client, tourist, police):
    _, ella_token = police()
    _, col_token = police("colombo-fort-police")
    ella = socketio.test_client(app, query_string=f"token={ella_token}")
    col = socketio.test_client(app, query_string=f"token={col_token}")
    ella.get_received(); col.get_received()
    client.post("/api/sos", json={"message": "my bag was stolen", "latitude": 6.87, "longitude": 81.05}, headers=tourist())
    assert _events(ella, "sos:new") and not _events(col, "sos:new")


def test_bad_token_cannot_connect(app):
    assert not socketio.test_client(app, query_string="token=nope").is_connected()
