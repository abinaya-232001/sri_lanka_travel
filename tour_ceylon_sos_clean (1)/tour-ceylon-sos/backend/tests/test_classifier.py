import pytest

from app.services.classifier import predict_incident

CASES = [
    ("Someone stole my phone at the bus stand", "theft"),
    ("My friend got bitten by a snake near Ella", "animal_attack"),
    ("my dad collapsed and isn't breathing", "medical"),
    ("the hotel is full of smoke and fire", "fire"),
    ("there is a man following me everywhere", "harassment"),
    ("I lost my passport in Kandy", "lost_passport"),
    ("our boat flipped and my son is in the water", "drowning"),
    ("a tuk tuk crashed into a bus and people are injured", "accident"),
    ("we are lost on the mountain trail and it is getting dark", "lost_rescue"),
    ("the river flooded and water is entering our hotel", "natural_disaster"),
    ("my daughter is missing since this morning", "missing_person"),
    ("a man punched me in the face outside the bar", "physical_assault"),
    ("the driver sexually assaulted me", "sexual_assault"),
    ("someone used my credit card without permission", "financial_fraud"),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_model(text, expected):
    assert predict_incident(text)["incident_type"] == expected


def test_single_word_is_not_classified():
    assert predict_incident("help") is None
