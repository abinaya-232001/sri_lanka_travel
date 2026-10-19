from pathlib import Path

_COMPONENTS = Path(__file__).resolve().parents[4]
_p = _COMPONENTS / "itinerary" / "backend" / "utils"
_s = str(_p)
if _p.is_dir() and _s not in __path__:
    __path__.append(_s)
