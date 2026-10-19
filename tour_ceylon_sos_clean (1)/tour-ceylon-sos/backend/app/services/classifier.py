"""Random Forest incident classifier for tourist SOS messages.

Loads ``app/ml/models/incident_rf.joblib`` once (lazily) and predicts the
incident type from the tourist's typed or transcribed message. If the model
file or scikit-learn is missing, ``predict_incident`` returns ``None`` and the
caller falls back to the old keyword rules, so an SOS is never blocked.

Train / retrain the model with:  python -m app.ml.train_incident_model
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "models" / "incident_rf.joblib"
DEFAULT_THRESHOLD = 0.40
MIN_WORDS = 2  # "help" alone carries no incident information

_lock = threading.Lock()
_bundle: dict[str, Any] | None = None
_load_failed = False


def _load() -> dict[str, Any] | None:
    global _bundle, _load_failed
    if _bundle is not None or _load_failed:
        return _bundle
    with _lock:
        if _bundle is not None or _load_failed:
            return _bundle
        try:
            import joblib

            _bundle = joblib.load(MODEL_PATH)
            try:  # one message at a time: threads only add latency
                _bundle["pipeline"].named_steps["rf"].n_jobs = 1
            except Exception:
                pass
            log.info("Incident RF model loaded (%s classes)", len(_bundle["classes"]))
        except Exception:  # missing file, sklearn not installed, version mismatch
            log.exception("Incident RF model unavailable at %s; keyword fallback will be used", MODEL_PATH)
            _load_failed = True
    return _bundle


def warm_up() -> bool:
    """Load the model at app start-up so the first SOS is not delayed (~3 s load)."""
    ok = model_available()
    if ok:
        predict_incident("warm up the incident model")
    return ok


def model_available() -> bool:
    return _load() is not None


def reload_model() -> bool:
    """Drop the cached model (e.g. after retraining) and load it again."""
    global _bundle, _load_failed
    with _lock:
        _bundle, _load_failed = None, False
    return model_available()


def predict_incident(text: str | None, top_k: int = 3) -> dict[str, Any] | None:
    """
    Classify a tourist message.

    Returns ``{"incident_type", "confidence", "is_confident", "alternatives",
    "matched_signals", "source"}`` or ``None`` when there is nothing to
    classify or the model is unavailable.
    """
    text = (text or "").strip()
    if len(text.split()) < MIN_WORDS:
        return None
    bundle = _load()
    if bundle is None:
        return None
    try:
        pipeline = bundle["pipeline"]
        proba = pipeline.predict_proba([text])[0]
        classes = list(pipeline.classes_)
    except Exception:
        log.exception("Incident RF prediction failed")
        return None

    ranked = sorted(((str(c), float(p)) for c, p in zip(classes, proba)), key=lambda item: item[1], reverse=True)
    best_type, best_p = ranked[0]
    threshold = float(bundle.get("confidence_threshold", DEFAULT_THRESHOLD))

    try:
        from app.ml.incident_features import lexicon_hits

        signals = lexicon_hits(text)
    except Exception:
        signals = {}

    return {
        "incident_type": best_type,
        "confidence": round(float(best_p), 4),
        "is_confident": bool(best_p >= threshold),
        "alternatives": [
            {"incident_type": label, "confidence": round(float(p), 4)} for label, p in ranked[1:top_k]
        ],
        "matched_signals": signals,
        "source": "random_forest",
    }


GENERIC_TYPES = {"general", "other", "police_assistance", "", None}


def resolve_incident_type(
    text: str | None,
    selected_type: str | None,
    *,
    english: bool = True,
) -> tuple[str | None, dict | None]:
    """
    Decide the incident type from the tourist's message and the SOS button they pressed.

    * Confident model prediction -> model wins (the message is the best evidence).
    * Low confidence + generic button (General SOS / Send message) -> use the
      model's best guess but mark it for officer review.
    * Low confidence + specific button -> keep the tourist's own choice.
    * No text or no model -> ``(None, None)`` so the caller can fall back.
    """
    result = predict_incident(text)
    if result is None:
        return None, None
    if not english:
        # The model is trained on English. If translation failed and we still
        # have foreign text, never trust the prediction on its own.
        result = {**result, "is_confident": False, "untranslated": True}
    selected = (selected_type or "").strip().lower() or None
    if result["is_confident"]:
        decided, reason = result["incident_type"], "model_confident"
    elif selected in GENERIC_TYPES:
        decided, reason = result["incident_type"], "model_low_confidence"
    else:
        decided, reason = selected, "kept_tourist_selection"
    details = {
        **result,
        "selected_type": selected,
        "decided_type": decided,
        "decision": reason,
        "needs_review": reason != "model_confident",
    }
    return decided, details
