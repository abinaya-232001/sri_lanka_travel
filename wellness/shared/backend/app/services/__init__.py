from pathlib import Path

_COMPONENTS = Path(__file__).resolve().parents[4]
for _rel in (
    ("itinerary", "backend", "services"),
    ("sos", "backend", "services"),
    ("wellness", "backend", "services"),
):
    _p = _COMPONENTS.joinpath(*_rel)
    _s = str(_p)
    if _p.is_dir() and _s not in __path__:
        __path__.append(_s)
