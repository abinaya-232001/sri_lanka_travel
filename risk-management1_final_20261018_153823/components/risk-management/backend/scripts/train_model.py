"""
train_model.py - trains and saves the crowd-score regressor and the risk classifier.

WHAT EACH METRIC MEANS (every metric written to disk is labelled with its split):
  site-holdout (PRIMARY, locked): 10 fixed destinations are removed from training and
      predicted by a separate, transient model. Tests generalisation to unseen sites.
  site-grouped CV (validation): 5 folds x 3 repeats over all 197 sites; each site is
      unseen exactly once per repeat. Same procedure as scripts/validate_model.py.
  random 80/20 split: the same destinations appear in train and test. Optimistic.
  5-fold CV (file order): cross_val_score(cv=5) with no shuffling. The data file is
      sorted by date, so each fold is a contiguous block of dates and every site is
      seen in training. Optimistic; NOT a test of unseen destinations.

THE TARGET IS SYNTHETIC (simulate_crowd_data.py). No metric here measures agreement
with real crowds.

THE DEPLOYED MODEL (models/crowd_pipeline.pkl) is trained on a random 80% of rows from
ALL 197 sites, including the 10 holdout sites. The site-holdout numbers come from a
separate model that is never saved.

Usage: python train_model.py [--skip-grid-search] [--skip-shap] [--allow-change]
  --skip-grid-search : use the locked hyperparameters directly (50 / 12 / 7)
  --skip-shap        : skip the SHAP plots
  --allow-change     : save even if hyperparameters or locked site-holdout numbers differ
"""
import argparse
import json
import os
import pickle
import platform
import shutil
import sys
import warnings
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (mean_absolute_error, r2_score, accuracy_score,
                             balanced_accuracy_score, classification_report, confusion_matrix)
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

try:
    import seaborn as sns
except Exception:
    sns = None
try:
    import shap
except Exception:
    shap = None

warnings.filterwarnings('ignore')

# Feature groups. Numeric features pass through unchanged; categorical features use
# OneHotEncoder(handle_unknown="ignore").
# WHY ONE-HOT: LabelEncoder gives nominal categories (category, season, district) an
# arbitrary integer order, which tree splits then treat as meaningful. One-hot removes
# that ordering artifact, and an unseen category at inference becomes an all-zero row
# instead of being silently mapped to label 0.
# NOTE: earlier versions of this comment and of the metadata quoted site-holdout R2
# values of 0.68-0.91 and "about 0.87-0.89" for the encoding experiment. Those came
# from an earlier experiment configuration and are NOT reproduced by the current
# pipeline. The verified one-hot site-holdout R2 is 0.3331 (scripts/validate_model.py).
NUMERIC_FEATURES = [
    'day_of_week', 'month', 'is_weekend', 'is_public_holiday', 'is_festival_period',
    'avg_temperature_c', 'avg_rainfall_mm', 'daily_flights_at_cmb', 'hotel_occupancy_rate',
    'capacity_per_day', 'is_eco_friendly', 'is_unesco', 'entrance_fee_lkr'
]
CATEGORICAL_FEATURES = ['category', 'season', 'district']
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

HOLDOUT_SITE_NAMES = [
    "Bentota Beach", "Bundala National Park", "Colombo Lotus Tower",
    "Kalpitiya Beach", "Kande Viharaya", "Kandy Lake",
    "Minneriya National Park", "Pasikuda Beach", "Tangalle Beach",
    "Wilpattu National Park"
]

# Locked values (do not change without an explicit decision).
LOCKED_PARAMS = {'n_estimators': 50, 'max_depth': 12, 'min_samples_split': 7}
LOCKED_SITE = {'mae': 0.1232, 'r2': 0.3331, 'acc': 0.7731, 'bacc': 0.5754}
GCV_FOLDS = 5
GCV_REPEATS = 3
GCV_SEED_BASE = 1000
# Reference from the validate_model.py run of 2026-10-01 (informational check only).
REFERENCE_GCV = {'r2_mean': 0.5071, 'mae_mean': 0.1159}

# Anchor all paths to the project root (this script lives in scripts\).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "master_dataset_fixed.csv")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


def _json_default(o):
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def make_preprocessor():
    return ColumnTransformer([
        ('num', 'passthrough', NUMERIC_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES)
    ])


def make_site_folds(site_ids, n_splits, seed):
    rng = np.random.RandomState(seed)
    s = np.array(sorted(site_ids))
    rng.shuffle(s)
    return [set(x.tolist()) for x in np.array_split(s, n_splits)]


def backup_existing(paths, stamp):
    existing = [p for p in paths if os.path.exists(p)]
    if not existing:
        return None
    dest = os.path.join(PROJECT_ROOT, "backups", "train_" + stamp)
    os.makedirs(dest, exist_ok=True)
    for p in existing:
        rel = os.path.relpath(p, PROJECT_ROOT).replace(os.sep, "__")
        shutil.copy2(p, os.path.join(dest, rel))
    return dest


def train_model(args):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print("TOURISM RISK SYSTEM - MODEL TRAINING REPORT (v3, pipeline-based)")
    print("=" * 60)

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # STEP 1: LOAD DATA
    print("\n[STEP 1] Loading master dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"  Total records: {len(df)}")
    print(f"  Total columns: {len(df.columns)}")
    date_sorted = bool(pd.to_datetime(df['date']).is_monotonic_increasing)
    print(f"  File sorted by date: {date_sorted}")

    overwritten = [os.path.join(MODELS_DIR, n) for n in (
        "crowd_pipeline.pkl", "risk_pipeline.pkl", "risk_label_encoder.pkl",
        "model_metadata.json", "model_metrics.json")]
    overwritten += [os.path.join(OUTPUTS_DIR, n) for n in (
        "confusion_matrix_site_holdout.png", "confusion_matrix.png", "actual_vs_predicted.png",
        "feature_importance.png", "shap_summary_plot.png", "shap_bar_plot.png")]
    bdir = backup_existing(overwritten, stamp)
    print(f"  Backed up files that this run may overwrite to: {bdir}")

    # STEP 2: TARGET ENCODING (target only - features use OneHotEncoder)
    print("\n[STEP 2] Encoding target label...")
    le_risk = LabelEncoder()
    df['risk_encoded'] = le_risk.fit_transform(df['risk_level'])
    print(f"  Risk classes: {list(le_risk.classes_)}")

    X = df[ALL_FEATURES]
    y_score = df['crowd_score_normalized']
    y_risk = df['risk_encoded']
    print(f"  Feature matrix shape: {X.shape}  ({len(NUMERIC_FEATURES)} numeric + {len(CATEGORICAL_FEATURES)} categorical)")

    # STEP 3: RANDOM 80/20 SPLIT (secondary, optimistic)
    print("\n[STEP 3] Random 80/20 split (secondary metric, optimistic)...")
    X_train, X_test, y_score_train, y_score_test = train_test_split(X, y_score, test_size=0.2, random_state=42)
    _, _, y_risk_train, y_risk_test = train_test_split(X, y_risk, test_size=0.2, random_state=42)
    print(f"  Training set: {len(X_train)} records")
    print(f"  Test set:     {len(X_test)} records")

    # STEP 3b: SITE-HOLDOUT SPLIT (PRIMARY metric)
    # crowd_score_normalized is generated in simulate_crowd_data.py as a formula of
    # (annual_visitors, capacity_per_day, season, is_weekend, is_public_holiday) + noise.
    # Several ingredients are also model features, so a random row split lets the model
    # memorise each site. Holding out entire destinations tests unseen sites.
    print("\n[STEP 3b] Site-holdout split (PRIMARY metric - unseen destinations)...")
    holdout_sites = set(df.loc[df['site_name'].isin(HOLDOUT_SITE_NAMES), 'site_id'].unique())
    missing_holdout = set(HOLDOUT_SITE_NAMES) - set(
        df.loc[df['site_id'].isin(holdout_sites), 'site_name'].unique()
    )
    if missing_holdout:
        raise ValueError(f"Fixed holdout sites not found in dataset: {missing_holdout}")
    site_train_mask = ~df['site_id'].isin(holdout_sites)
    site_test_mask = df['site_id'].isin(holdout_sites)

    X_site_train, y_score_site_train = X[site_train_mask], y_score[site_train_mask]
    X_site_test, y_score_site_test = X[site_test_mask], y_score[site_test_mask]
    y_risk_site_train, y_risk_site_test = y_risk[site_train_mask], y_risk[site_test_mask]

    print(f"  Train sites: {df.loc[site_train_mask, 'site_id'].nunique()} ({site_train_mask.sum()} rows)")
    print(f"  Held-out (unseen) sites: {df.loc[site_test_mask, 'site_id'].nunique()} ({site_test_mask.sum()} rows)")
    print(f"  Held-out site names: {sorted(df.loc[site_test_mask, 'site_name'].unique())}")

    # STEP 4: BASELINE (mean predictor, random-split test set)
    print("\n[STEP 4] Baseline (mean predictor, random-split test set)...")
    baseline_pred = np.full(len(y_score_test), y_score_train.mean())
    baseline_mae = mean_absolute_error(y_score_test, baseline_pred)
    baseline_r2 = r2_score(y_score_test, baseline_pred)
    print(f"  Baseline MAE: {baseline_mae:.4f}  R2: {baseline_r2:.4f}   (split: random 80/20)")

    # STEP 5: HYPERPARAMETERS
    # NOTE (honest labelling): this grid search runs on X_train, a random 80% of ALL rows,
    # so it includes rows from the 10 holdout sites, and its 3 folds are random rows, not
    # grouped by site. scripts/validate_model.py (Section 6) re-ran the search with
    # site-grouped folds and no holdout sites: it selected near-identical settings
    # (inner MAE 0.1153 vs 0.1155; holdout R2 0.3351 vs 0.3331), so the locked parameters
    # are kept. Do not change them because of a holdout score.
    if args.skip_grid_search:
        print("\n[STEP 5] Skipping grid search; using locked hyperparameters...")
        best_params = dict(LOCKED_PARAMS)
    else:
        print("\n[STEP 5] Hyperparameter tuning with Grid Search (random-row folds, includes holdout sites)...")
        param_grid = {
            'model__n_estimators': [50, 100, 150],
            'model__max_depth': [8, 10, 12],
            'model__min_samples_split': [3, 5, 7]
        }
        reg_pipeline = Pipeline([
            ('pre', make_preprocessor()),
            ('model', RandomForestRegressor(random_state=42, n_jobs=-1))
        ])
        grid_search = GridSearchCV(reg_pipeline, param_grid, cv=3,
                                    scoring='neg_mean_absolute_error', n_jobs=-1, verbose=0)
        grid_search.fit(X_train, y_score_train)
        best_params = {k.replace('model__', ''): int(v) for k, v in grid_search.best_params_.items()}
        print(f"  Best CV MAE (random split): {-grid_search.best_score_:.4f}")
    print(f"  Hyperparameters in use: {best_params}")
    if best_params != LOCKED_PARAMS and not args.allow_change:
        print(f"  STOP: hyperparameters differ from the locked {LOCKED_PARAMS}. Nothing was saved to models/.")
        print("        Re-run with --allow-change only if you deliberately want to change them.")
        sys.exit(3)

    def make_regressor():
        return RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)

    def make_classifier():
        return RandomForestClassifier(**best_params, random_state=42, n_jobs=-1, class_weight="balanced")

    # STEP 6: FIT DEPLOYMENT PIPELINES on random-split training data
    print("\n[STEP 6] Fitting deployment pipelines on random-split training data...")
    crowd_pipeline = Pipeline([('pre', make_preprocessor()), ('model', make_regressor())])
    crowd_pipeline.fit(X_train, y_score_train)
    y_pred_score = crowd_pipeline.predict(X_test)
    mae = mean_absolute_error(y_score_test, y_pred_score)
    r2 = r2_score(y_score_test, y_pred_score)

    y_pred_score_train = crowd_pipeline.predict(X_train)
    train_mae = mean_absolute_error(y_score_train, y_pred_score_train)
    train_r2 = r2_score(y_score_train, y_pred_score_train)
    print(f"  Random-split test  MAE={mae:.4f} R2={r2:.4f}")
    print(f"  Random-split train MAE={train_mae:.4f} R2={train_r2:.4f}")

    risk_pipeline = Pipeline([('pre', make_preprocessor()), ('model', make_classifier())])
    risk_pipeline.fit(X_train, y_risk_train)
    y_pred_risk = risk_pipeline.predict(X_test)
    y_pred_risk_train = risk_pipeline.predict(X_train)
    train_accuracy = accuracy_score(y_risk_train, y_pred_risk_train)
    test_accuracy = accuracy_score(y_risk_test, y_pred_risk)
    test_balanced_accuracy = balanced_accuracy_score(y_risk_test, y_pred_risk)
    print(f"  Random-split classification: train_acc={train_accuracy:.4f} test_acc={test_accuracy:.4f} balanced_acc={test_balanced_accuracy:.4f}")
    print("\n" + classification_report(y_risk_test, y_pred_risk, target_names=le_risk.classes_))

    # STEP 7: 5-FOLD CV, no shuffling, file order (cross_val_score cv=5 on a regressor).
    # Because the file is date-sorted, each fold is a contiguous block of dates and all
    # sites are seen in training. This is NOT a test of unseen destinations.
    print("\n[STEP 7] 5-fold CV, unshuffled / file order (contiguous date blocks, all sites seen)...")
    cv_pipeline = Pipeline([('pre', make_preprocessor()), ('model', make_regressor())])
    cv_mae_scores = cross_val_score(cv_pipeline, X, y_score, cv=5, scoring='neg_mean_absolute_error', n_jobs=-1)
    cv_r2_scores = cross_val_score(cv_pipeline, X, y_score, cv=5, scoring='r2', n_jobs=-1)
    cv_mae, cv_mae_std = -cv_mae_scores.mean(), cv_mae_scores.std()
    cv_r2, cv_r2_std = cv_r2_scores.mean(), cv_r2_scores.std()
    print(f"  Date-block CV MAE: {cv_mae:.4f} (+/- {cv_mae_std:.4f})")
    print(f"  Date-block CV R2:  {cv_r2:.4f} (+/- {cv_r2_std:.4f})")

    # STEP 7b: SITE-GROUPED CV over all sites (same procedure as validate_model.py)
    print(f"\n[STEP 7b] Site-grouped CV over all sites ({GCV_FOLDS} folds x {GCV_REPEATS} repeats)...")
    all_site_ids = sorted(df['site_id'].unique().tolist())
    gcv_mae_list, gcv_r2_list = [], []
    for rep in range(GCV_REPEATS):
        for fold_sites in make_site_folds(all_site_ids, GCV_FOLDS, GCV_SEED_BASE + rep):
            te_mask = df['site_id'].isin(fold_sites).values
            m = Pipeline([('pre', make_preprocessor()), ('model', make_regressor())])
            m.fit(X[~te_mask], y_score[~te_mask])
            p = np.clip(m.predict(X[te_mask]), 0.0, 1.0)
            gcv_mae_list.append(mean_absolute_error(y_score[te_mask], p))
            gcv_r2_list.append(r2_score(y_score[te_mask], p))
        print(f"  repeat {rep} done")
    gcv_mae_mean, gcv_mae_sd = float(np.mean(gcv_mae_list)), float(np.std(gcv_mae_list, ddof=1))
    gcv_r2_mean, gcv_r2_sd = float(np.mean(gcv_r2_list)), float(np.std(gcv_r2_list, ddof=1))
    print(f"  Site-grouped CV MAE: {gcv_mae_mean:.4f} (sd {gcv_mae_sd:.4f})")
    print(f"  Site-grouped CV R2:  {gcv_r2_mean:.4f} (sd {gcv_r2_sd:.4f}, min {min(gcv_r2_list):.4f}, max {max(gcv_r2_list):.4f})")
    gcv_match = (abs(gcv_r2_mean - REFERENCE_GCV['r2_mean']) < 0.0005
                 and abs(gcv_mae_mean - REFERENCE_GCV['mae_mean']) < 0.0005)
    print(f"  validate_model.py reference (2026-10-01): R2 {REFERENCE_GCV['r2_mean']:.4f}, MAE {REFERENCE_GCV['mae_mean']:.4f} -> "
          + ("MATCH" if gcv_match else "DIFFERENT"))

    # STEP 8: SITE-HOLDOUT EVALUATION (PRIMARY metric, same hyperparameters)
    print("\n[STEP 8] Site-holdout evaluation (PRIMARY metric)...")
    site_reg_pipeline = Pipeline([('pre', make_preprocessor()), ('model', make_regressor())])
    site_reg_pipeline.fit(X_site_train, y_score_site_train)
    y_pred_site = site_reg_pipeline.predict(X_site_test)
    site_holdout_mae = mean_absolute_error(y_score_site_test, y_pred_site)
    site_holdout_r2 = r2_score(y_score_site_test, y_pred_site)
    site_base_pred = np.full(len(y_score_site_test), y_score_site_train.mean())
    site_holdout_baseline_mae = mean_absolute_error(y_score_site_test, site_base_pred)
    site_holdout_baseline_r2 = r2_score(y_score_site_test, site_base_pred)

    site_clf_pipeline = Pipeline([('pre', make_preprocessor()), ('model', make_classifier())])
    site_clf_pipeline.fit(X_site_train, y_risk_site_train)
    y_pred_risk_site = site_clf_pipeline.predict(X_site_test)
    site_holdout_accuracy = accuracy_score(y_risk_site_test, y_pred_risk_site)
    site_holdout_balanced_accuracy = balanced_accuracy_score(y_risk_site_test, y_pred_risk_site)

    _cm_labels = sorted(set(y_risk_site_test.tolist()) | set(y_pred_risk_site.tolist()))
    _cm = confusion_matrix(y_risk_site_test, y_pred_risk_site, labels=_cm_labels)
    _cm_names = [str(le_risk.classes_[i]) for i in _cm_labels]
    print(f"  Site-holdout confusion matrix (labels {_cm_labels} = {_cm_names}):")
    print(_cm)
    plt.figure(figsize=(9, 8))
    if sns is not None:
        sns.heatmap(_cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=_cm_names, yticklabels=_cm_names,
                    annot_kws={"weight": "bold"})
    else:
        plt.imshow(_cm, cmap='Blues')
        plt.xticks(range(len(_cm_names)), _cm_names)
        plt.yticks(range(len(_cm_names)), _cm_names)
        for i in range(_cm.shape[0]):
            for j in range(_cm.shape[1]):
                plt.text(j, i, str(_cm[i, j]), ha='center', va='center', fontweight='bold')
    plt.title('Confusion Matrix - Risk Level Classification (site-holdout)\nTourism Risk & Context Intelligence System')
    plt.xlabel('Predicted Risk Level')
    plt.ylabel('Actual Risk Level')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'confusion_matrix_site_holdout.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print('  Saved: outputs/confusion_matrix_site_holdout.png')

    print(f"  Site-holdout MAE: {site_holdout_mae:.4f}   (mean-predictor MAE {site_holdout_baseline_mae:.4f}, R2 {site_holdout_baseline_r2:.4f})")
    print(f"  Site-holdout R2:  {site_holdout_r2:.4f}")
    print(f"  Site-holdout classification accuracy: {site_holdout_accuracy:.4f}  balanced: {site_holdout_balanced_accuracy:.4f}")

    locked_ok = (abs(round(site_holdout_mae, 4) - LOCKED_SITE['mae']) < 1e-9
                 and abs(round(site_holdout_r2, 4) - LOCKED_SITE['r2']) < 1e-9
                 and abs(round(site_holdout_accuracy, 4) - LOCKED_SITE['acc']) < 1e-9
                 and abs(round(site_holdout_balanced_accuracy, 4) - LOCKED_SITE['bacc']) < 1e-9)
    print("  Locked site-holdout numbers reproduced: " + ("YES" if locked_ok else "NO"))
    if not locked_ok and not args.allow_change:
        print("  STOP: site-holdout numbers differ from the locked values. Nothing was saved to models/.")
        print("        Re-run with --allow-change only if you deliberately want to change them.")
        sys.exit(3)

    # STEP 9: CONFUSION MATRIX (random split)
    print("\n[STEP 9] Confusion matrix (random split)...")
    cm = confusion_matrix(y_risk_test, y_pred_risk)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, cmap='Blues')
    classes = le_risk.classes_
    ax.set_xticks(range(len(classes))); ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, fontsize=12); ax.set_yticklabels(classes, fontsize=12)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, str(cm[i, j]), ha='center', va='center', fontsize=14, fontweight='bold',
                     color='white' if cm[i, j] > cm.max() / 2 else 'black')
    ax.set_xlabel('Predicted Risk Level'); ax.set_ylabel('Actual Risk Level')
    ax.set_title('Confusion Matrix - Risk Level Classification (random split)\nTourism Risk & Context Intelligence System')
    plt.colorbar(im); plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "confusion_matrix.png"), dpi=150, bbox_inches='tight'); plt.close()
    print("  Saved: outputs/confusion_matrix.png")

    # STEP 10: ACTUAL VS PREDICTED PLOT
    print("\n[STEP 10] Actual vs predicted plot...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sample_size = min(500, len(y_score_test))
    idx = np.random.RandomState(0).choice(len(y_score_test), sample_size, replace=False)
    actual_sample = y_score_test.iloc[idx]
    predicted_sample = np.asarray(y_pred_score)[idx]
    axes[0].scatter(actual_sample, predicted_sample, alpha=0.4, color='#3b82f6', s=20)
    axes[0].plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect prediction')
    axes[0].set_xlabel('Actual Crowd Score'); axes[0].set_ylabel('Predicted Crowd Score')
    axes[0].set_title(f'Actual vs Predicted (random split, optimistic)\nMAE={mae:.4f}, R2={r2:.4f}')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    models_ = ['Baseline\n(mean, random)', 'RF - random\nsplit', 'RF - site\nholdout']
    mae_scores = [baseline_mae, mae, site_holdout_mae]
    r2_scores = [baseline_r2, r2, site_holdout_r2]
    x = np.arange(3); width = 0.35
    bars1 = axes[1].bar(x - width/2, mae_scores, width, label='MAE (lower=better)', color=['#ef4444', '#22c55e', '#f97316'])
    bars2 = axes[1].bar(x + width/2, r2_scores, width, label='R2 (higher=better)', color=['#f59e0b', '#3b82f6', '#a855f7'])
    axes[1].set_xticks(x); axes[1].set_xticklabels(models_, fontsize=10)
    axes[1].set_title('Baseline vs Random-split vs Site-holdout')
    axes[1].legend(); axes[1].grid(True, alpha=0.3, axis='y')
    for bar in list(bars1) + list(bars2):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                      f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "actual_vs_predicted.png"), dpi=150, bbox_inches='tight'); plt.close()
    print("  Saved: outputs/actual_vs_predicted.png")

    # STEP 11: FEATURE IMPORTANCE (transformed/one-hot feature names)
    print("\n[STEP 11] Feature importance (post-encoding names)...")
    fitted_pre = crowd_pipeline.named_steps['pre']
    fitted_model = crowd_pipeline.named_steps['model']
    feature_names_out = list(fitted_pre.get_feature_names_out())
    importance_df = pd.DataFrame({
        'feature': feature_names_out,
        'importance': fitted_model.feature_importances_
    }).sort_values('importance', ascending=True).tail(25)

    fig, ax = plt.subplots(figsize=(10, 9))
    ax.barh(importance_df['feature'], importance_df['importance'], color='#6366f1')
    ax.set_xlabel('Feature Importance Score (Gini)')
    ax.set_title('Random Forest Feature Importance (top 25, post-OneHot)\nTourism Risk & Context Intelligence System')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, "feature_importance.png"), dpi=150, bbox_inches='tight'); plt.close()
    print("  Saved: outputs/feature_importance.png")

    # STEP 12: SHAP (optional)
    print("\n[STEP 12] SHAP analysis (pipeline-adapted)...")
    if shap is None or args.skip_shap:
        print("  SHAP skipped (not installed or --skip-shap); everything else is unaffected.")
    else:
        try:
            X_test_transformed = fitted_pre.transform(X_test.iloc[:200])
            if hasattr(X_test_transformed, "toarray"):
                X_test_transformed = X_test_transformed.toarray()
            explainer = shap.TreeExplainer(fitted_model)
            shap_values = explainer.shap_values(X_test_transformed)

            plt.figure(figsize=(10, 8))
            shap.summary_plot(shap_values, X_test_transformed, feature_names=feature_names_out, show=False)
            plt.title("SHAP Feature Importance\nTourism Risk & Context Intelligence System")
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUTS_DIR, "shap_summary_plot.png"), dpi=150, bbox_inches='tight'); plt.close()

            plt.figure(figsize=(10, 6))
            shap.summary_plot(shap_values, X_test_transformed, feature_names=feature_names_out, plot_type="bar", show=False)
            plt.title("SHAP Mean Feature Impact\nTourism Risk & Context Intelligence System")
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUTS_DIR, "shap_bar_plot.png"), dpi=150, bbox_inches='tight'); plt.close()
            print("  Saved: outputs/shap_summary_plot.png, outputs/shap_bar_plot.png")
        except Exception as e:
            print(f"  WARNING: SHAP step failed ({e}); skipping SHAP outputs, everything else is unaffected.")

    # STEP 13: SAVE PIPELINES + METADATA
    print("\n[STEP 13] Saving pipelines and metadata...")
    with open(os.path.join(MODELS_DIR, "crowd_pipeline.pkl"), "wb") as f:
        pickle.dump(crowd_pipeline, f)
    with open(os.path.join(MODELS_DIR, "risk_pipeline.pkl"), "wb") as f:
        pickle.dump(risk_pipeline, f)
    with open(os.path.join(MODELS_DIR, "risk_label_encoder.pkl"), "wb") as f:
        pickle.dump(le_risk, f)

    cv_description = (
        "5-fold CV without shuffling, in file order. The data file is sorted by date, so each fold is a "
        "contiguous block of dates and every site appears in training. Optimistic; not a test of unseen destinations."
        if date_sorted else
        "5-fold CV without shuffling, in file order (file is not date-sorted; fold composition not verified)."
    )
    metadata = {
        "metadata_schema_version": 2,
        "model_version": "v3.0-pipeline",
        "training_timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "source_dataset": os.path.basename(DATA_PATH),
        "source_dataset_records": len(df),
        "feature_list_raw": ALL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features_onehot": CATEGORICAL_FEATURES,
        "transformed_feature_count": len(feature_names_out),
        "target_definition": {
            "crowd_score_normalized": "SYNTHETIC. Formula: (annual_visitors/365 * season_mult * weekend_mult * holiday_mult * noise) / capacity_per_day, clipped to [0,1]. See simulate_crowd_data.py. Not an observed real-world value.",
            "risk_level": "Threshold of crowd_score_normalized (>=0.75 High, >=0.45 Medium, else Low)."
        },
        "target_leakage_note": (
            "is_weekend, is_public_holiday, season and capacity_per_day are direct ingredients of the "
            "generating formula and are also model features; hotel_occupancy_rate and daily_flights_at_cmb "
            "are generated from the same drivers. Measured with scripts/validate_model.py (2026-10-01): "
            "dropping capacity_per_day lowered site-holdout R2 from 0.3331 to -0.3630 and site-grouped CV "
            "(repeat 0, 5 folds) R2 from 0.555 to 0.295, so skill on unseen destinations depends mainly on "
            "this formula ingredient. Dropping occupancy+flights, is_weekend+is_public_holiday, or season "
            "individually changed R2 by about 0.01 or less, but month and day_of_week still carry equivalent "
            "information, so those tests cannot show the features are harmless. Random-split and date-block "
            "metrics are optimistic; report site-holdout and site-grouped CV."
        ),
        "encoding_note": (
            "OneHotEncoder(handle_unknown='ignore') is used for category/season/district instead of "
            "LabelEncoder, to avoid an arbitrary integer ordering of nominal categories and to encode an unseen "
            "category as an all-zero row instead of silently mapping it to 0. Earlier notes quoted site-holdout "
            "R2 values of 0.68-0.91 and about 0.87-0.89; those came from an earlier experiment configuration and "
            "are NOT reproduced by this pipeline. The verified site-holdout R2 with this encoding is 0.3331."
        ),
        "hyperparameter_selection_note": (
            "n_estimators=50, max_depth=12, min_samples_split=7 were chosen by a 3-fold random-row GridSearchCV "
            "on a random 80% split that included the 10 holdout sites (values lie on the grid edge). "
            "scripts/validate_model.py Section 6 repeated the search with site-grouped folds and no holdout sites: "
            "it selected near-identical settings (inner MAE 0.1153 vs 0.1155; holdout R2 0.3351 vs 0.3331), so the "
            "parameters are locked."
        ),
        "deployment_model_note": (
            "models/crowd_pipeline.pkl and risk_pipeline.pkl are trained on a random 80% of rows from all 197 "
            "sites, including the 10 holdout sites. The site-holdout metrics come from a separate model trained "
            "without those sites, which is not saved."
        ),
        "best_hyperparameters": best_params,
        "primary_reported_metric": "site_holdout",
        "site_holdout_evaluation": {
            "description": "Entire sites held out of training. Tests generalization to unseen destinations (10 fixed sites: 4 Beach, 4 Nature, 1 Heritage, 1 Religious; harder than average).",
            "train_sites": int(df.loc[site_train_mask, 'site_id'].nunique()),
            "test_sites": int(df.loc[site_test_mask, 'site_id'].nunique()),
            "held_out_site_names": sorted(df.loc[site_test_mask, 'site_name'].unique().tolist()),
            "train_records": int(site_train_mask.sum()),
            "test_records": int(site_test_mask.sum()),
            "regression_mae": round(site_holdout_mae, 4),
            "regression_r2": round(site_holdout_r2, 4),
            "regression_baseline_mae": round(site_holdout_baseline_mae, 4),
            "regression_baseline_r2": round(site_holdout_baseline_r2, 4),
            "classification_accuracy": round(site_holdout_accuracy, 4),
            "classification_balanced_accuracy": round(site_holdout_balanced_accuracy, 4)
        },
        "site_grouped_cv_evaluation": {
            "description": f"Site-grouped CV over all {len(all_site_ids)} sites, {GCV_FOLDS} folds x {GCV_REPEATS} repeats; every site is unseen once per repeat. Folds overlap across repeats, so the sd is a spread, not a confidence interval.",
            "n_folds_total": len(gcv_r2_list),
            "mae_mean": round(gcv_mae_mean, 4),
            "mae_sd": round(gcv_mae_sd, 4),
            "r2_mean": round(gcv_r2_mean, 4),
            "r2_sd": round(gcv_r2_sd, 4),
            "r2_min": round(float(min(gcv_r2_list)), 4),
            "r2_max": round(float(max(gcv_r2_list)), 4)
        },
        "date_block_cv_evaluation": {
            "description": cv_description,
            "cv_mae": round(cv_mae, 4),
            "cv_mae_std": round(cv_mae_std, 4),
            "cv_r2": round(cv_r2, 4),
            "cv_r2_std": round(cv_r2_std, 4)
        },
        "random_split_evaluation": {
            "description": "Random 80/20 row split. The same sites appear in train and test, so this is optimistic (site-level memorisation plus formula ingredients). Do not report as the primary metric.",
            "train_records": len(X_train),
            "test_records": len(X_test),
            "regression_mae": round(mae, 4),
            "regression_r2": round(r2, 4),
            "regression_train_mae": round(train_mae, 4),
            "regression_train_r2": round(train_r2, 4),
            "classification_train_accuracy": round(train_accuracy, 4),
            "classification_test_accuracy": round(test_accuracy, 4),
            "classification_test_balanced_accuracy": round(test_balanced_accuracy, 4),
            "baseline_mae": round(baseline_mae, 4),
            "baseline_r2": round(baseline_r2, 4)
        },
        "independent_validation": {
            "script": "scripts/validate_model.py",
            "outputs": ["outputs/validation_results.json", "outputs/validation_summary.csv",
                        "outputs/validation_per_site.csv", "outputs/validation_per_category.csv",
                        "outputs/validation_r2_comparison.png"],
            "note": "Temporal 2024->2025, baselines, ablation, shuffled-target check, error analysis and calibration are computed there, not here."
        },
        "limitations": [
            "crowd_score_normalized is synthetic; no metric measures agreement with real crowds.",
            "Skill on unseen destinations depends heavily on capacity_per_day, an ingredient of the target's generating formula.",
            "Errors on unseen destinations are mostly site-level offsets; annual visitors is not a model input.",
            "Temporal 2024->2025 validation is nearly identical to a random split because the simulator reuses one formula in both years.",
            "The deployed model was trained on rows from all 197 sites, including the 10 holdout sites."
        ],
        "risk_classes": list(le_risk.classes_)
    }
    with open(os.path.join(MODELS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2, default=_json_default)

    # model_metrics.json is read by app.py /model-metrics and by tourism-unified RiskPage.js,
    # which expects FLAT keys: accuracy, r2, mae, cv_mae, n_estimators, max_depth,
    # min_samples_split, features_used. A missing or zero key makes the page show a stale
    # hard-coded fallback, so every one of them must be present and non-zero.
    metrics_flat = {
        "model_type": "Random Forest",
        "metrics_basis": "site-holdout (10 unseen destinations)",
        "n_estimators": int(best_params['n_estimators']),
        "max_depth": int(best_params['max_depth']),
        "min_samples_split": int(best_params['min_samples_split']),
        "features_used": len(ALL_FEATURES),
        "train_records": int(site_train_mask.sum()),
        "test_records": int(site_test_mask.sum()),
        "mae": round(site_holdout_mae, 4),
        "r2": round(site_holdout_r2, 4),
        "accuracy": round(site_holdout_accuracy, 4),
        "balanced_accuracy": round(site_holdout_balanced_accuracy, 4),
        "baseline_mae": round(site_holdout_baseline_mae, 4),
        "baseline_r2": round(site_holdout_baseline_r2, 4),
        "cv_mae": round(gcv_mae_mean, 4),
        "cv_mae_std": round(gcv_mae_sd, 4),
        "cv_r2": round(gcv_r2_mean, 4),
        "cv_r2_std": round(gcv_r2_sd, 4),
        "cv_basis": f"site-grouped CV, {len(all_site_ids)} sites, {GCV_FOLDS} folds x {GCV_REPEATS} repeats",
        "random_split_r2_optimistic": round(r2, 4),
        "random_split_mae_optimistic": round(mae, 4),
        "target_is_synthetic": True,
        "metric_labels": {
            "mae": "site-holdout", "r2": "site-holdout", "accuracy": "site-holdout",
            "cv_mae": "site-grouped CV", "cv_r2": "site-grouped CV"
        },
        "full_details_file": "models/model_metadata.json",
        "training_timestamp": metadata["training_timestamp"]
    }
    with open(os.path.join(MODELS_DIR, "model_metrics.json"), "w") as f:
        json.dump(metrics_flat, f, indent=2, default=_json_default)
    print("  Saved: models/crowd_pipeline.pkl, models/risk_pipeline.pkl, models/risk_label_encoder.pkl,")
    print("         models/model_metadata.json (nested, full detail), models/model_metrics.json (flat, for the app)")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE (every metric is labelled with its split)")
    print("=" * 60)
    print(f"  site-holdout (10 unseen sites, PRIMARY): MAE={site_holdout_mae:.4f} R2={site_holdout_r2:.4f} acc={site_holdout_accuracy:.4f} bal_acc={site_holdout_balanced_accuracy:.4f}")
    print(f"  site-grouped CV (197 sites, 15 folds):   MAE={gcv_mae_mean:.4f} R2={gcv_r2_mean:.4f} (sd {gcv_r2_sd:.4f})")
    print(f"  date-block 5-fold CV (optimistic):       MAE={cv_mae:.4f} R2={cv_r2:.4f}")
    print(f"  random 80/20 split (optimistic):         MAE={mae:.4f} R2={r2:.4f} acc={test_accuracy:.4f}")
    print("  Target is synthetic. Restart the backend so it loads the new pickles.")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-grid-search", action="store_true")
    ap.add_argument("--skip-shap", action="store_true")
    ap.add_argument("--allow-change", action="store_true")
    args = ap.parse_args()
    train_model(args)


if __name__ == "__main__":
    main()
