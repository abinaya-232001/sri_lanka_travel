"""WhatsApp alert to the tourist's family right after SOS.

Automatic sending needs the WhatsApp Business API (here: Twilio).
WHATSAPP_MODE=console only prints the message (development). In every case the
tourist app also gets a wa.me link per contact as a one-tap fallback.
"""

from __future__ import annotations

import json
import logging
from urllib.parse import quote

from flask import current_app

log = logging.getLogger(__name__)


def normalize_phone(phone: str | None) -> str | None:
    """E.164 (+<country><number>). Local numbers like 077... are rejected: WhatsApp needs the country code."""
    if not phone:
        return None
    digits = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    elif digits.startswith("0") or not digits:
        return None
    if not digits.startswith("+"):
        digits = "+" + digits
    return digits if 9 <= len(digits) <= 16 else None


def build_message(incident, lat=None, lng=None) -> tuple[str, dict]:
    tourist = incident.tourist
    label = (incident.guidance or {}).get("label", "Emergency")
    station = incident.station
    police = f"{station.name} ({station.telephone or '119'})" if station else "Sri Lanka Police (119)"
    if lat is None or lng is None:
        ping = incident.latest_ping()
        lat = ping.latitude if ping else incident.start_lat
        lng = ping.longitude if ping else incident.start_lng
    link = f"https://maps.google.com/?q={lat:.6f},{lng:.6f}"
    words = (incident.message_original or incident.message_english or "").strip() or "SOS pressed. No written message."
    body = (
        f"SOS from {tourist.name} in Sri Lanka\n"
        f"Message: {words}\n"
        f"Location: {link}\n"
        f"Emergency: {label}\n"
        f"Police alerted: {police}\n"
        f"Sri Lanka Police: 119."
    )
    return body, {"1": tourist.name, "2": words, "3": link, "4": police}


def _send_twilio(to: str, body: str, variables: dict) -> tuple[bool, str | None]:
    cfg = current_app.config
    sid, token, sender = cfg.get("TWILIO_ACCOUNT_SID"), cfg.get("TWILIO_AUTH_TOKEN"), cfg.get("TWILIO_WHATSAPP_FROM")
    if not (sid and token and sender):
        return False, "Twilio WhatsApp not configured"
    try:
        from twilio.rest import Client

        kwargs = {"from_": sender if sender.startswith("whatsapp:") else f"whatsapp:{sender}", "to": f"whatsapp:{to}"}
        if cfg.get("TWILIO_WHATSAPP_CONTENT_SID"):  # approved template (required in production)
            kwargs.update(content_sid=cfg["TWILIO_WHATSAPP_CONTENT_SID"], content_variables=json.dumps(variables))
        else:
            kwargs["body"] = body
        Client(sid, token).messages.create(**kwargs)
        return True, None
    except Exception as exc:
        return False, str(exc)


def alert_family(incident, contacts=None, lat=None, lng=None) -> dict:
    body, variables = build_message(incident, lat, lng)
    mode = current_app.config.get("WHATSAPP_MODE", "console")
    results = []
    for contact in (contacts if contacts is not None else incident.tourist.family_contacts):
        if mode == "twilio":
            delivered, error = _send_twilio(contact.phone, body, variables)
        else:
            log.info("[WhatsApp console] to %s:\n%s", contact.phone, body)
            delivered, error = False, "console mode"
        results.append({
            "id": contact.id,
            "name": contact.name,
            "phone": contact.phone,
            "delivered": delivered,
            "error": error,
            "whatsapp_link": f"https://wa.me/{contact.phone.lstrip('+')}?text={quote(body)}",
        })
    return {"recipients": results, "delivered": any(r["delivered"] for r in results), "message": body}
