"""Train the Random Forest incident classifier for Tour Ceylon SOS.

Usage (from the folder that contains the ``app`` package):

    python -m app.ml.train_incident_model
    python -m app.ml.train_incident_model --data path/to/dataset.csv

Outputs:
    app/ml/models/incident_rf.joblib        the trained pipeline
    app/ml/models/incident_rf_metrics.json  evaluation report

Evaluation is done on *handwritten* messages only: each fold trains on all
generated messages plus 4/5 of the handwritten ones and tests on the remaining
handwritten fifth. Generated messages are never used as test data, because
they share templates and would make the score look better than it is.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import FeatureUnion, Pipeline

from app.ml.incident_features import LexiconFeatures

ML_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = ML_DIR.parent.parent / "data" / "tourist_incident_dataset.csv"
MODEL_PATH = ML_DIR / "models" / "incident_rf.joblib"
METRICS_PATH = ML_DIR / "models" / "incident_rf_metrics.json"
CONFIDENCE_THRESHOLD = 0.40


def build_pipeline(random_state: int = 42) -> Pipeline:
    text = Pipeline([
        ("tfidf", FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)),
        ])),
        ("select", SelectKBest(chi2, k=2000)),
    ])
    return Pipeline([
        ("features", FeatureUnion([("text", text), ("lexicon", LexiconFeatures())])),
        ("rf", RandomForestClassifier(
            n_estimators=200,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=random_state,
        )),
    ])


def load_dataset(path: Path):
    texts, labels, sources = [], [], []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            msg = (row.get("Tourist Message") or "").strip()
            label = (row.get("Incident Type ID") or "").strip()
            if msg and label:
                texts.append(msg)
                labels.append(label)
                sources.append((row.get("Source") or "handwritten").strip().lower())
    return np.array(texts, dtype=object), np.array(labels), np.array(sources)


def evaluate(texts, labels, sources, folds: int = 5) -> dict:
    hand = np.where(sources == "handwritten")[0]
    gen = np.where(sources != "handwritten")[0]
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=1)
    y_true, y_pred, conf = [], [], []
    for k, (tr, te) in enumerate(skf.split(texts[hand], labels[hand]), start=1):
        train_idx = np.concatenate([gen, hand[tr]])
        test_idx = hand[te]
        model = build_pipeline().fit(texts[train_idx], labels[train_idx])
        proba = model.predict_proba(texts[test_idx])
        pred = model.classes_[proba.argmax(axis=1)]
        y_true += list(labels[test_idx]); y_pred += list(pred); conf += list(proba.max(axis=1))
        print(f"  fold {k}/{folds}: accuracy {np.mean(pred == labels[test_idx]):.3f}")
    y_true, y_pred, conf = np.array(y_true), np.array(y_pred), np.array(conf)
    correct = y_true == y_pred
    confident = conf >= CONFIDENCE_THRESHOLD
    classes = sorted(set(labels))
    return {
        "evaluated_on": f"{len(y_true)} handwritten messages ({folds}-fold, generated messages never tested)",
        "accuracy": round(float(correct.mean()), 4),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "share_above_threshold": round(float(confident.mean()), 4),
        "accuracy_above_threshold": round(float(correct[confident].mean()), 4) if confident.any() else None,
        "accuracy_below_threshold": round(float(correct[~confident].mean()), 4) if (~confident).any() else None,
        "per_class": classification_report(y_true, y_pred, labels=classes, output_dict=True, zero_division=0),
        "confusion_matrix": {"labels": classes, "matrix": confusion_matrix(y_true, y_pred, labels=classes).tolist()},
        "top_confusions": [
            {"true": a, "predicted": b, "count": n}
            for (a, b), n in Counter((a, b) for a, b in zip(y_true, y_pred) if a != b).most_common(10)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--skip-eval", action="store_true")
    args = parser.parse_args()

    texts, labels, sources = load_dataset(args.data)
    print(f"Loaded {len(texts)} messages, {len(set(labels))} incident types from {args.data}")

    metrics = {}
    if not args.skip_eval:
        print("Evaluating on handwritten messages...")
        metrics = evaluate(texts, labels, sources)
        print(f"Accuracy: {metrics['accuracy']:.3f}  |  "
              f"confident share {metrics['share_above_threshold']:.2f}, "
              f"accuracy when confident {metrics['accuracy_above_threshold']}")

    print("Training final model on all data...")
    model = build_pipeline().fit(texts, labels)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "pipeline": model,
        "classes": list(model.classes_),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "n_training_messages": int(len(texts)),
    }, MODEL_PATH, compress=("xz", 9))
    metrics.update({
        "model": "TF-IDF (word + char, chi2 top 2000) + incident lexicon -> RandomForest(200 trees)",
        "n_training_messages": int(len(texts)),
        "class_counts": dict(Counter(labels.tolist())),
        "sklearn_version": sklearn.__version__,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    })
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
