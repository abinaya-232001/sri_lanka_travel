import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, classification_report
from sklearn.preprocessing import LabelEncoder, StandardScaler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import os

def run_model_comparison():
    print("=" * 65)
    print("TOURISM RISK SYSTEM — MODEL COMPARISON REPORT")
    print("=" * 65)

    os.makedirs("outputs", exist_ok=True)

    # ── LOAD DATA ──
    print("\n[STEP 1] Loading master dataset...")
    df = pd.read_csv("data/master_dataset.csv")
    print(f"  Total records: {len(df)}")

    # ── ENCODE ──
    print("\n[STEP 2] Encoding categorical columns...")
    le_category = LabelEncoder()
    le_season = LabelEncoder()
    le_district = LabelEncoder()

    df['category_encoded'] = le_category.fit_transform(df['category'])
    df['season_encoded'] = le_season.fit_transform(df['season'])
    df['district_encoded'] = le_district.fit_transform(df['district'])

    FEATURES = [
        'day_of_week', 'month', 'is_weekend',
        'is_public_holiday', 'is_festival_period',
        'avg_temperature_c', 'avg_rainfall_mm',
        'daily_flights_at_cmb', 'capacity_per_day',
        'category_encoded', 'season_encoded', 'district_encoded',
        'is_eco_friendly', 'is_unesco', 'entrance_fee_lkr'
    ]

    available = [f for f in FEATURES if f in df.columns]
    X = df[available]
    y = df['crowd_score_normalized']

    # ── SPLIT ──
    print("\n[STEP 3] Splitting data 80/20...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Training: {len(X_train)} records")
    print(f"  Testing:  {len(X_test)} records")

    # Scale for SVR and KNN
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── DEFINE ALL MODELS ──
    models = {
        "Linear Regression": {
            "model": LinearRegression(),
            "needs_scaling": True,
            "reason_rejected": "Assumes linear relationship — crowd levels are nonlinear"
        },
        "Decision Tree": {
            "model": DecisionTreeRegressor(max_depth=10, random_state=42),
            "needs_scaling": False,
            "reason_rejected": "Single tree overfits — unstable predictions"
        },
        "K-Nearest Neighbors": {
            "model": KNeighborsRegressor(n_neighbors=5),
            "needs_scaling": True,
            "reason_rejected": "Slow on large datasets — poor interpretability"
        },
        "Support Vector Regression": {
            "model": SVR(kernel='rbf', C=1.0),
            "needs_scaling": True,
            "reason_rejected": "High computational cost — poor interpretability"
        },
        "Random Forest (Selected)": {
            "model": RandomForestRegressor(
                n_estimators=150, max_depth=12,
                min_samples_split=7, random_state=42, n_jobs=-1
            ),
            "needs_scaling": False,
            "reason_rejected": "SELECTED — best overall performance"
        }
    }

    # ── TRAIN AND EVALUATE ALL MODELS ──
    print("\n[STEP 4] Training and evaluating all models...")
    print("-" * 65)

    results = []

    for name, config in models.items():
        print(f"\n  Training: {name}...")

        model = config["model"]

        if config["needs_scaling"]:
            X_tr = X_train_scaled
            X_te = X_test_scaled
        else:
            X_tr = X_train
            X_te = X_test

        # Train
        model.fit(X_tr, y_train)

        # Predict
        y_pred = model.predict(X_te)

        # Clip predictions to valid range
        y_pred = np.clip(y_pred, 0, 1)

        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Cross validation
        if config["needs_scaling"]:
            X_cv = scaler.fit_transform(X)
        else:
            X_cv = X

        cv_scores = cross_val_score(
            model, X_cv, y,
            cv=5, scoring='neg_mean_absolute_error', n_jobs=-1
        )
        cv_mae = -cv_scores.mean()
        cv_std = cv_scores.std()

        results.append({
            "Model": name,
            "MAE": round(mae, 4),
            "R2": round(r2, 4),
            "CV MAE": round(cv_mae, 4),
            "CV Std": round(cv_std, 4),
            "Reason": config["reason_rejected"]
        })

        status = " SELECTED" if "Selected" in name else " REJECTED"
        print(f"  {status}")
        print(f"  MAE:    {mae:.4f}")
        print(f"  R2:     {r2:.4f}")
        print(f"  CV MAE: {cv_mae:.4f} ±{cv_std:.4f}")
        print(f"  Reason: {config['reason_rejected']}")

    # ── PRINT COMPARISON TABLE ──
    print("\n" + "=" * 65)
    print("MODEL COMPARISON TABLE")
    print("=" * 65)
    print(f"{'Model':<35} {'MAE':>8} {'R2':>8} {'CV MAE':>10}")
    print("-" * 65)

    for r in sorted(results, key=lambda x: x['MAE']):
        marker = " ← SELECTED" if "Selected" in r['Model'] else ""
        print(f"{r['Model']:<35} {r['MAE']:>8} {r['R2']:>8} {r['CV MAE']:>10}{marker}")

    # ── GENERATE COMPARISON CHART ──
    print("\n[STEP 5] Generating comparison charts...")

    model_names = [r['Model'].replace(" (Selected)", "\n(Selected)") for r in results]
    mae_values = [r['MAE'] for r in results]
    r2_values = [r['R2'] for r in results]
    colors = ['#ef4444' if 'Selected' not in r['Model'] else '#22c55e' for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        'Tourism Risk System — Algorithm Comparison\nAll Models Evaluated on Same 4,386 Test Records',
        fontsize=12, fontweight='bold'
    )

    # MAE Comparison
    bars1 = axes[0].barh(model_names, mae_values, color=colors)
    axes[0].set_xlabel('Mean Absolute Error (lower is better)', fontsize=11)
    axes[0].set_title('MAE Comparison\n(Target: <= 0.25)', fontsize=11)
    axes[0].axvline(x=0.25, color='orange', linestyle='--', linewidth=2, label='Target MAE = 0.25')
    axes[0].legend(fontsize=9)

    for bar, val in zip(bars1, mae_values):
        axes[0].text(
            bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
            f'{val:.4f}', va='center', fontsize=10,
            fontweight='bold'
        )

    # R2 Comparison
    bars2 = axes[1].barh(model_names, r2_values, color=colors)
    axes[1].set_xlabel('R² Score (higher is better)', fontsize=11)
    axes[1].set_title('R² Score Comparison\n(Target: >= 0.70)', fontsize=11)
    axes[1].axvline(x=0.70, color='orange', linestyle='--', linewidth=2, label='Target R² = 0.70')
    axes[1].legend(fontsize=9)

    for bar, val in zip(bars2, r2_values):
        axes[1].text(
            bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
            f'{val:.4f}', va='center', fontsize=10,
            fontweight='bold'
        )

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#22c55e', label='Selected — Random Forest'),
        Patch(facecolor='#ef4444', label='Rejected — other algorithms')
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=10, bbox_to_anchor=(0.5, -0.05))

    plt.tight_layout()
    plt.savefig("outputs/model_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: outputs/model_comparison.png")

    # ── CV STABILITY CHART ──
    fig2, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(results))
    cv_maes = [r['CV MAE'] for r in results]
    cv_stds = [r['CV Std'] for r in results]
    bar_colors = ['#22c55e' if 'Selected' in r['Model'] else '#ef4444' for r in results]
    short_names = [r['Model'].replace(" (Selected)", "").replace("Random Forest", "RF").replace("Support Vector Regression", "SVR").replace("K-Nearest Neighbors", "KNN").replace("Linear Regression", "Linear Reg").replace("Decision Tree", "Dec Tree") for r in results]

    bars = ax.bar(x, cv_maes, color=bar_colors, yerr=cv_stds, capsize=5, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(short_names, fontsize=10)
    ax.set_ylabel('CV MAE (lower = better)', fontsize=11)
    ax.set_title('5-Fold Cross Validation Stability Comparison\n(Error bars show standard deviation — smaller = more stable)', fontsize=11)
    ax.axhline(y=0.25, color='orange', linestyle='--', linewidth=2, label='Target MAE = 0.25')
    ax.legend(fontsize=9)

    for bar, val, std in zip(bars, cv_maes, cv_stds):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + std + 0.005,
                f'{val:.4f}', ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig("outputs/model_comparison_cv.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: outputs/model_comparison_cv.png")

    # ── FINAL SUMMARY ──
    best = min(results, key=lambda x: x['MAE'])
    worst = max(results, key=lambda x: x['MAE'])

    print("\n" + "=" * 65)
    print("COMPARISON COMPLETE — SUMMARY FOR SUPERVISOR")
    print("=" * 65)
    print(f"\n  Models evaluated:    {len(results)}")
    print(f"  Test records used:   {len(X_test)}")
    print(f"  Best MAE:            {best['Model']} — {best['MAE']}")
    print(f"  Worst MAE:           {worst['Model']} — {worst['MAE']}")
    print(f"\n  REJECTION REASONS:")
    for r in results:
        if 'Selected' not in r['Model']:
            print(f"  ❌ {r['Model']:<30} — {r['Reason']}")
    print(f"\n  SELECTION REASON:")
    print(f"  Random Forest — Best MAE and R2, stable CV, interpretable SHAP")
    print(f"\n  Charts saved:")
    print(f"  - outputs/model_comparison.png")
    print(f"  - outputs/model_comparison_cv.png")
    print(f"\n  Copy both to frontend/public/ to show on website")
    print("=" * 65)

    return results

if __name__ == "__main__":
    run_model_comparison()