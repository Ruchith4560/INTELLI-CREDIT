"""
╔══════════════════════════════════════════════════════════════════╗
║  Intelli-Credit — XGBoost Credit Model Trainer                  ║
║                                                                  ║
║  Run this script ONCE to create the ML model file.              ║
║                                                                  ║
║  HOW TO RUN:                                                     ║
║    cd intelli-credit/backend                                     ║
║    pip install xgboost scikit-learn joblib pandas numpy          ║
║    python train_model.py                                         ║
║                                                                  ║
║  OUTPUT:  models/credit_model.pkl                                ║
║  After this, the scoring engine uses real XGBoost predictions.   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import joblib

# ─── Create output folder ─────────────────────────────────────────────────────
os.makedirs("models", exist_ok=True)

print("=" * 60)
print("  Intelli-Credit — Training XGBoost Credit Risk Model")
print("=" * 60)

# ─── Generate synthetic training data ─────────────────────────────────────────
# In production: replace this with real historical loan data
np.random.seed(42)
N = 1000   # number of training samples

print(f"\n📊 Generating {N} synthetic credit samples...")

data = pd.DataFrame({
    # Feature 1: Debt-to-Equity ratio  (0.1 – 3.5)
    "debt_to_equity":    np.random.beta(2, 4, N) * 3.5 + 0.1,

    # Feature 2: Current Ratio  (0.5 – 3.5)
    "current_ratio":     np.random.beta(3, 2, N) * 3.0 + 0.5,

    # Feature 3: Interest Coverage Ratio  (0.5 – 8.0)
    "interest_coverage": np.random.beta(3, 2, N) * 7.5 + 0.5,

    # Feature 4: EBITDA Margin %  (2 – 30)
    "ebitda_margin":     np.random.beta(2, 3, N) * 28 + 2,

    # Feature 5: GST Mismatch %  (0 – 25)
    "gst_mismatch":      np.random.exponential(3, N).clip(0, 25),

    # Feature 6: Cheque Bounce Rate %  (0 – 8)
    "bounce_rate":       np.random.exponential(1, N).clip(0, 8),

    # Feature 7: News Sentiment Score  (0.1 – 0.9)
    "news_sentiment":    np.random.beta(3, 2, N) * 0.8 + 0.1,

    # Feature 8: Active Litigation Cases  (0 – 10)
    "litigation_count":  np.random.poisson(1.5, N).clip(0, 10),
})

# ─── Create realistic default labels ──────────────────────────────────────────
# A company defaults if it has multiple bad signals simultaneously
risk_signals = (
    (data["debt_to_equity"]    > 2.0).astype(int) * 2 +
    (data["current_ratio"]     < 1.0).astype(int) * 2 +
    (data["interest_coverage"] < 1.5).astype(int) * 3 +
    (data["ebitda_margin"]     < 5.0).astype(int) * 1 +
    (data["gst_mismatch"]      > 12.0).astype(int) * 2 +
    (data["bounce_rate"]       > 4.0).astype(int) * 2 +
    (data["news_sentiment"]    < 0.25).astype(int) * 1 +
    (data["litigation_count"]  > 5).astype(int) * 2
)

# Default if total risk signal score >= 4
data["default"] = (risk_signals >= 4).astype(int)

default_rate = data["default"].mean()
print(f"   Default rate in training data: {default_rate:.1%}")
print(f"   Approve cases: {(data['default']==0).sum()}  |  Default cases: {(data['default']==1).sum()}")

# ─── Train / Test split ────────────────────────────────────────────────────────
X = data.drop("default", axis=1)
y = data["default"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\n📂 Train: {len(X_train)} samples  |  Test: {len(X_test)} samples")

# ─── Train XGBoost model ───────────────────────────────────────────────────────
print("\n🤖 Training XGBoost model...")

try:
    from xgboost import XGBClassifier

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),  # handle imbalance
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # ─── Evaluate ─────────────────────────────────────────────────────────────
    y_pred      = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc_roc  = roc_auc_score(y_test, y_pred_proba)

    print(f"\n📈 Model Performance:")
    print(f"   Accuracy:  {accuracy:.2%}")
    print(f"   AUC-ROC:   {auc_roc:.4f}")
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Approve", "Default"]))

    # ─── Feature importance ────────────────────────────────────────────────────
    print("🔍 Feature Importances (XGBoost):")
    importances = dict(zip(X.columns, model.feature_importances_))
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"   {feat:<22} {bar}  {imp:.4f}")

    # ─── Save model ───────────────────────────────────────────────────────────
    model_path = "models/credit_model.pkl"
    joblib.dump(model, model_path)
    print(f"\n✅ Model saved to: {model_path}")
    print("   Restart the backend server to use the new model.")

except ImportError:
    print("\n❌ XGBoost not installed.")
    print("   Run:  pip install xgboost")
    print("   Then re-run this script.")
    exit(1)

# ─── Also try LightGBM as alternative ─────────────────────────────────────────
try:
    import lightgbm as lgb

    lgb_model = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        num_leaves=31,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    lgb_model.fit(X_train, y_train)
    lgb_auc = roc_auc_score(y_test, lgb_model.predict_proba(X_test)[:, 1])
    joblib.dump(lgb_model, "models/credit_model_lgb.pkl")
    print(f"\n✅ LightGBM model also saved (AUC: {lgb_auc:.4f})")
    print("   To use LightGBM, rename credit_model_lgb.pkl → credit_model.pkl")

except ImportError:
    print("\nℹ️  LightGBM not installed (optional). Run: pip install lightgbm")

print("\n" + "=" * 60)
print("  Training complete!  Run the backend and test the app.")
print("=" * 60)
