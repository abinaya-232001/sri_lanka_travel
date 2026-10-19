"""Tourist-facing guidance for each incident type.

After the Random Forest model identifies the incident, the tourist dashboard
shows: a highlighted safety tip, the nearest police station's phone number,
and the hotlines relevant to that incident (plus nearest hospital, tourism
police desk or embassy when they apply).

Hotline numbers: Police 119, Suwa Seriya ambulance 1990, Fire & Rescue 110,
Disaster Management Centre 117. Verify against official sources before going
live and keep this file as the single place to update them.
"""

from __future__ import annotations

from typing import Any

HOTLINES = {
    "police": {"label": "Police Emergency", "number": "119"},
    "ambulance": {"label": "Suwa Seriya Ambulance", "number": "1990"},
    "fire": {"label": "Fire & Rescue", "number": "110"},
    "dmc": {"label": "Disaster Management Centre", "number": "117"},
}

# alert_to:  where the SOS alert goes (the nearest police station always gets it)
# hotlines:  national numbers shown to the tourist, most relevant first
# needs:     extra nearby services to look up for this incident
GUIDANCE: dict[str, dict[str, Any]] = {
    "fire": {
        "label": "Fire",
        "tip": "Leave the building immediately if safe, use the stairs (never the lift), stay low under smoke, and do not go back inside.",
        "steps": ["Close doors behind you to slow the fire.", "If trapped, seal the door gap with cloth and signal from a window.", "Meet others at a safe spot away from the building."],
        "hotlines": ["fire", "police", "ambulance"],
        "alert_to": ["Nearest Police Station", "Fire & Rescue Service (110)"],
        "needs": [],
        "severity": "critical",
    },
    "accident": {
        "label": "Road Accident",
        "tip": "Move away from traffic if you can, switch on hazard lights, and do not move anyone who is seriously injured.",
        "steps": ["Check breathing and press firmly on any heavy bleeding.", "Keep injured people warm and still.", "Note vehicle numbers and take photos if it is safe."],
        "hotlines": ["ambulance", "police"],
        "alert_to": ["Nearest Police Station", "Suwa Seriya Ambulance (1990)", "Nearest Government Hospital"],
        "needs": ["hospital"],
        "severity": "critical",
    },
    "medical": {
        "label": "Medical Emergency",
        "tip": "Call an ambulance now, stay with the person, keep them still and follow the dispatcher's instructions.",
        "steps": ["If they are not breathing, start CPR.", "Tell responders about allergies, medicines and conditions.", "Keep your phone line free for the ambulance."],
        "hotlines": ["ambulance", "police"],
        "alert_to": ["Nearest Police Station", "Suwa Seriya Ambulance (1990)", "Nearest Government Hospital"],
        "needs": ["hospital"],
        "severity": "critical",
    },
    "sexual_assault": {
        "label": "Sexual Assault",
        "tip": "Get to a safe place with people around you. If possible, do not wash or change clothes before a medical check, and ask for a female officer if you prefer.",
        "steps": ["Stay with someone you trust.", "Keep any clothing or items as evidence.", "You can get medical care even before deciding on a police report."],
        "hotlines": ["police", "ambulance"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station", "Nearest Government Hospital"],
        "needs": ["tourism_police", "hospital"],
        "severity": "critical",
    },
    "theft": {
        "label": "Theft / Robbery",
        "tip": "Do not chase or confront the thief. Block your bank cards immediately and keep any receipts or photos for the police report.",
        "steps": ["Write down what was taken and when.", "Use 'Find my phone' to lock or locate a stolen phone.", "Ask the station for a police report for insurance."],
        "hotlines": ["police"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station"],
        "needs": ["tourism_police"],
        "severity": "high",
    },
    "physical_assault": {
        "label": "Physical Assault",
        "tip": "Move away from the attacker to a busy, staffed place. Press firmly on any bleeding wound and wait for police or medical help.",
        "steps": ["Do not fight back unless you must to escape.", "Remember the attacker's description.", "Get injuries checked even if they seem minor."],
        "hotlines": ["police", "ambulance"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station", "Nearest Government Hospital"],
        "needs": ["tourism_police", "hospital"],
        "severity": "critical",
    },
    "natural_disaster": {
        "label": "Natural Disaster",
        "tip": "Follow official warnings, move to higher ground or a designated shelter, and keep away from rivers, the sea and steep slopes.",
        "steps": ["Do not walk or drive through floodwater.", "For a tsunami warning, move inland and uphill immediately.", "Keep your phone charged and location on."],
        "hotlines": ["dmc", "police", "ambulance"],
        "alert_to": ["Nearest Police Station", "Disaster Management Centre (117)"],
        "needs": [],
        "severity": "critical",
    },
    "missing_person": {
        "label": "Missing Person",
        "tip": "Tell police right away. Share a recent photo, what the person was wearing, and the place and time they were last seen.",
        "steps": ["Stay at the last known place if someone else can search.", "Keep calling and messaging their phone.", "Check with your hotel and tour operator."],
        "hotlines": ["police"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station"],
        "needs": ["tourism_police"],
        "severity": "high",
    },
    "lost_rescue": {
        "label": "Lost / Rescue Required",
        "tip": "Stay where you are if it is safe, keep your location sharing on, save phone battery, and avoid steep or unknown paths.",
        "steps": ["Turn down screen brightness and close other apps.", "Make yourself visible with bright clothing or a light.", "Stay together as a group."],
        "hotlines": ["police", "dmc", "ambulance"],
        "alert_to": ["Nearest Police Station", "Disaster Management Centre (117)"],
        "needs": [],
        "severity": "high",
    },
    "harassment": {
        "label": "Harassment / Threat",
        "tip": "Go to a busy, staffed place such as a hotel lobby or shop, do not engage with the person, and keep your phone ready.",
        "steps": ["Tell staff nearby that you feel unsafe.", "Save threatening messages or photos as evidence.", "Avoid walking alone until police respond."],
        "hotlines": ["police"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station"],
        "needs": ["tourism_police"],
        "severity": "high",
    },
    "animal_attack": {
        "label": "Animal Attack",
        "tip": "Move away from the animal. For a snakebite, keep still, keep the bitten limb below the heart, do not cut or suck the wound, and get to hospital fast.",
        "steps": ["Wash dog or monkey bites with soap and water for 15 minutes; rabies treatment is needed.", "Note the animal's appearance for doctors.", "Remove rings or tight items near the bite."],
        "hotlines": ["ambulance", "police"],
        "alert_to": ["Nearest Police Station", "Suwa Seriya Ambulance (1990)", "Nearest Government Hospital"],
        "needs": ["hospital"],
        "severity": "high",
    },
    "drowning": {
        "label": "Drowning / Water Emergency",
        "tip": "Shout for help and throw something that floats. Do not swim into dangerous water yourself; start CPR if the person is not breathing.",
        "steps": ["Alert lifeguards or boat operators nearby.", "Keep watching the person's position in the water.", "Once out, keep them warm and on their side if breathing."],
        "hotlines": ["police", "ambulance"],
        "alert_to": ["Nearest Police Station", "Suwa Seriya Ambulance (1990)", "Nearest Government Hospital"],
        "needs": ["hospital"],
        "severity": "critical",
    },
    "lost_passport": {
        "label": "Lost Passport / Documents",
        "tip": "Get a police report for the loss, then contact your embassy or high commission for an emergency travel document.",
        "steps": ["Keep a photo or copy of your passport if you have one.", "Tell your airline if you are flying soon.", "Inform your hotel, as they recorded your passport."],
        "hotlines": ["police"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station"],
        "needs": ["tourism_police"],
        "severity": "medium",
    },
    "financial_fraud": {
        "label": "Financial Fraud",
        "tip": "Call your bank's official number to block your cards, do not send more money, and keep all messages and receipts as evidence.",
        "steps": ["Change passwords for banking and email.", "Do not share OTP codes with anyone.", "Report the fraud to police for a reference number."],
        "hotlines": ["police"],
        "alert_to": ["Nearest Police Station", "Nearest Tourism Police Station"],
        "needs": ["tourism_police"],
        "severity": "medium",
    },
    "other": {
        "label": "Other Emergency",
        "tip": "Move to safety if you can, keep your location sharing on, and stay reachable on your phone.",
        "steps": ["Tell police what is happening in the chat as soon as you can.", "Stay away from crowds, smoke or damaged buildings."],
        "hotlines": ["police", "ambulance"],
        "alert_to": ["Nearest Police Station"],
        "needs": [],
        "severity": "high",
    },
}

ALIASES = {"general": "other"}


def guidance_key(incident_type: str | None) -> str:
    key = (incident_type or "other").strip().lower()
    key = ALIASES.get(key, key)
    return key if key in GUIDANCE else "other"


def _entry(kind, name, number, distance_km, lat=None, lng=None) -> dict:
    return {
        "kind": kind,
        "name": name,
        "number": number,
        "distance_km": round(float(distance_km), 2) if distance_km is not None else None,
        "latitude": lat,
        "longitude": lng,
    }


def build_guidance(incident_type: str | None, *, lat: float, lng: float, station=None,
                   station_distance_km: float | None = None, classification: dict | None = None) -> dict[str, Any]:
    """Tip, steps, nearest police number, nearby services and hotlines for the tourist dashboard."""
    from app.models import Hospital, Station
    from app.services.routing import nearest

    key = guidance_key(incident_type)
    g = GUIDANCE[key]
    police = _entry("nearest_police", station.name, station.telephone or "119", station_distance_km,
                    station.latitude, station.longitude) if station else None
    nearby = [police] if police else []

    if "tourism_police" in g["needs"]:
        tp, d = nearest(lat, lng, Station.query.filter_by(kind=Station.KIND_TOURISM).all())
        if tp is not None and (station is None or tp.id != station.id) and d <= 75:
            nearby.append(_entry("tourism_police", tp.name, tp.telephone, d, tp.latitude, tp.longitude))
    if "hospital" in g["needs"]:
        h, d = nearest(lat, lng, Hospital.query.all())
        if h is not None:
            nearby.append(_entry("nearest_hospital", h.name, h.phone, d, h.latitude, h.longitude))

    return {
        "incident_type": key,
        "label": g["label"],
        "severity": g["severity"],
        "tip": g["tip"],
        "steps": g["steps"],
        "alert_sent_to": g["alert_to"],
        "nearest_police": police,
        "nearby_contacts": nearby,
        "hotlines": [{"kind": k, **HOTLINES[k]} for k in g["hotlines"]],
        "classification": classification,
    }
