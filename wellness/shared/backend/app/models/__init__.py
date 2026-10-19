from pathlib import Path

_COMPONENTS = Path(__file__).resolve().parents[4]
for _rel in (
    ("itinerary", "backend", "models"),
    ("wellness", "backend", "models"),
):
    _p = _COMPONENTS.joinpath(*_rel)
    _s = str(_p)
    if _p.is_dir() and _s not in __path__:
        __path__.append(_s)

from app.models.accommodation import Accommodation
from app.models.attraction import Attraction
from app.models.budget_split import BudgetSplit
from app.models.business_directory import BusinessDirectory
from app.models.generated_itinerary import GeneratedItinerary
from app.models.saved_reference import SavedReference
from app.models.tourist_guide import TouristGuide
from app.models.travel_agency import TravelAgency
from app.models.user import User
from app.models.user_trip_input import UserTripInput
from app.models.wellness import (
    WellnessCenter,
    WellnessConditionMapping,
    WellnessMatchingSession,
    WellnessReview,
)

__all__ = [
    "User",
    "Accommodation",
    "Attraction",
    "BusinessDirectory",
    "TravelAgency",
    "TouristGuide",
    "UserTripInput",
    "BudgetSplit",
    "GeneratedItinerary",
    "SavedReference",
    "WellnessCenter",
    "WellnessReview",
    "WellnessConditionMapping",
    "WellnessMatchingSession",
]
