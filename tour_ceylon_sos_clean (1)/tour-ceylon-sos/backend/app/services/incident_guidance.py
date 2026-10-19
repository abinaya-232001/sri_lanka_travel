"""Apply the existing incident model to a new tourist message and refresh the tips.

The model file is only read. Nothing here trains or edits it.
"""

import re

from app.services.classifier import resolve_incident_type
from app.services.guidance import build_guidance

# The trained model is unsure about this short wording (it does not reach its
# confidence line). These are the same situations its harassment guidance covers.
_PERSON_CHASING = re.compile(r"\bchas(?:e|ed|ing)\b", re.I)
_ANIMAL = re.compile(r"\b(?:dog|snake|monkey|elephant|animal|bull|cow|leopard|bear|boar)s?\b", re.I)


def _type_for_message(english: str):
    decided, details = resolve_incident_type(english, "other", english=True)
    if not details:
        return None, None
    if details.get("is_confident"):
        return decided, details
    if _PERSON_CHASING.search(english) and not _ANIMAL.search(english):
        return "harassment", {
            "incident_type": "harassment",
            "decision": "message_words",
            "needs_review": False,
            "is_confident": True,
            "source": "message_words",
        }
    return decided, {**details, "needs_review": True}


def refresh_guidance_from_message(incident, english: str | None) -> bool:
    """Rebuild tips and contact numbers from one new message."""
    english = (english or "").strip()
    if not english:
        return False
    chosen, details = _type_for_message(english)
    if not chosen or not details:
        return False
    if chosen == incident.incident_type and not (incident.classification or {}).get("needs_review"):
        return False
    incident.incident_type = chosen
    incident.classification = details
    if english not in (incident.message_english or ""):
        incident.message_english = " ".join(filter(None, [incident.message_english, english])).strip()
    if english not in (incident.message_original or ""):
        incident.message_original = " ".join(filter(None, [incident.message_original, english])).strip()
    incident.guidance = build_guidance(
        chosen,
        lat=incident.start_lat,
        lng=incident.start_lng,
        station=incident.station,
        station_distance_km=incident.distance_km,
        classification=incident.classification,
    )
    return True
