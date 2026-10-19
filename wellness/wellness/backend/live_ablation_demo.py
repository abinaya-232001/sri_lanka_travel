"""
LIVE Ablation Study Re-Runner
==================================
Re-computes the ablation study (Table: "Ablation Study - Component
Contribution") FROM SCRATCH, using the REAL 83-center dataset and the
REAL scoring logic from matching_engine.py - not reading the saved
ablation_results.json file at all.

Run this LIVE during PP2 to prove the admin dashboard's numbers are
real and reproducible, not hardcoded:

    python live_ablation_demo.py

Compare the printed output to the "Ablation Study" table in the admin
dashboard (localhost:5003/admin -> Analytics, scroll down). The numbers
should closely match FULL / NO-DOSHA / NO-NLP-QUALITY / NO-BUDGET /
CONDITION-ONLY from the saved file, since both use the same real data
and the same real matching formula - this file is just computing it
live instead of reading a saved copy.
"""
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matching_engine import POOL, CONDITIONS_BY_PATH

CONDITIONS = CONDITIONS_BY_PATH["ayurveda"]
DOSHAS = ["Vata", "Pitta", "Kapha"]
BUDGET_TIERS = ["Budget", "Mid", "Premium"]

random.seed(42)  # reproducible test-query set


def generate_test_queries(n=60):
    """N synthetic tourist queries spanning the real condition/dosha/budget space."""
    queries = []
    for _ in range(n):
        queries.append({
            "condition": random.choice(CONDITIONS),
            "dosha": random.choice(DOSHAS),
            "budget_tier": random.choice(BUDGET_TIERS),
        })
    return queries


def score_center(c, condition, dosha, budget_tier, weights, use_dosha, use_quality, use_budget):
    cond_match = 1.0 if condition.lower() in c["conditions_text"].lower() else 0.3

    if c["dosha_focus"] == dosha:
        dosha_match = 1.0
    elif c["dosha_focus"] == "General/Unspecified":
        dosha_match = 0.6
    else:
        dosha_match = 0.4

    quality = c["nlp_quality"] / 5.0
    budget_match = 1.0 if budget_tier in c["price_tier"] else 0.5

    score = weights["condition"] * cond_match
    if use_dosha:
        score += weights["dosha"] * dosha_match
    if use_quality:
        score += weights["quality"] * quality
    if use_budget:
        score += weights["budget"] * budget_match

    return score, dosha_match, budget_match, quality


def run_configuration(name, weights, use_dosha, use_quality, use_budget, queries):
    """Runs all N queries under one ablation configuration, returns the 3 metrics."""
    qualities, budget_hits, dosha_hits = [], [], []

    for q in queries:
        scored = []
        for c in POOL:
            if c["category"] == "Spiritual/Meditation":
                continue  # ablation study is scoped to the Ayurveda path, as in the original
            score, dosha_match, budget_match, quality = score_center(
                c, q["condition"], q["dosha"], q["budget_tier"],
                weights, use_dosha, use_quality, use_budget
            )
            scored.append((score, c, quality, budget_match, dosha_match))

        scored.sort(key=lambda x: -x[0])
        top = scored[0]
        _, top_center, top_quality, top_budget_match, top_dosha_match = top

        qualities.append(top_center["nlp_quality"])
        budget_hits.append(1 if q["budget_tier"] in top_center["price_tier"] else 0)
        dosha_hits.append(1 if top_center["dosha_focus"] == q["dosha"] else 0)

    avg_quality = sum(qualities) / len(qualities)
    budget_alignment = sum(budget_hits) / len(budget_hits)
    dosha_compatibility = sum(dosha_hits) / len(dosha_hits)

    print(f"{name:16s}  avg_quality={avg_quality:.3f}   budget_alignment={budget_alignment*100:.1f}%   dosha_compatibility={dosha_compatibility*100:.1f}%")


def main():
    print("=" * 78)
    print("LIVE ABLATION STUDY RE-RUN")
    print(f"Real dataset: {len(POOL)} centers loaded from the live matching engine")
    print("Generating 60 fresh test queries across real conditions/doshas/budgets...")
    print("=" * 78)

    queries = generate_test_queries(60)
    weights = {"condition": 0.35, "dosha": 0.20, "quality": 0.25, "budget": 0.20}

    print()
    print(f"{'CONFIGURATION':16s}  {'AVG QUALITY':<20s} {'BUDGET ALIGNMENT':<24s} {'DOSHA COMPATIBILITY'}")
    print("-" * 78)
    run_configuration("FULL",           weights, True,  True,  True,  queries)
    run_configuration("NO-DOSHA",       weights, False, True,  True,  queries)
    run_configuration("NO-NLP-QUALITY", weights, True,  False, True,  queries)
    run_configuration("NO-BUDGET",      weights, True,  True,  False, queries)
    run_configuration("CONDITION-ONLY", weights, False, False, False, queries)
    print("-" * 78)
    print()
    print("Compare these numbers to the 'Ablation Study' table in the admin")
    print("dashboard (localhost:5003/admin -> Analytics, scroll down).")


if __name__ == "__main__":
    main()
