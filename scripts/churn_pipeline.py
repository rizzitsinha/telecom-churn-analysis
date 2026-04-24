"""
churn_pipeline.py
Trains a multiclass churn model (Stayed / Bundle_Switch / Company_Churn).
Outputs: churn_model.pkl, churn_predictions.csv, shap_values.npy, shap_feature_names.npy
"""

import os
import numpy as np
import pandas as pd
import pickle
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import (
    TargetEncoder, OrdinalEncoder, OneHotEncoder, StandardScaler
)
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from xgboost import XGBClassifier
import shap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(os.path.join(SCRIPT_DIR, "telecom_churn_data.csv"))
print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")

# ── Feature Engineering ────────────────────────────────────────────────────
print("Feature engineering...")

# Binary: irregular recharge
df["is_irregular_recharge"] = (df["recharge_frequency"] == "Irregular").astype(int)

# ARPU per tenure
df["arpu_per_tenure"] = (df["monthly_arpu"] / (df["tenure_months"] + 1)).round(4)

# Support tickets per month
df["support_per_month"] = (df["support_tickets_6mo"] / 6).round(4)

# Explode OTT platforms into binary columns
for ott in ["Hotstar", "Netflix", "Prime", "SonyLiv", "Zee5", "Disney"]:
    df[f"ott_{ott}"] = df["ott_platforms"].fillna("").str.contains(ott).astype(int)

# ── Prepare X and y ───────────────────────────────────────────────────────
DROP_COLS = [
    "customer_id", "churn", "churn_probability_score",
    "seasonal_churn_multiplier", "churn_type",
    "ott_platforms", "total_revenue_ltv",  # derived / leakage
    "recharge_frequency",  # replaced by is_irregular_recharge
]

y = df["churn_type"]
X = df.drop(columns=DROP_COLS)

print(f"  Features: {X.shape[1]}, Target classes: {y.nunique()}")

# ── Column groups ──────────────────────────────────────────────────────────
target_encode_cols = ["region", "bundle_name", "complaint_resolved"]
ordinal_cols = ["plan_tier"]
ordinal_categories = [
    ["Prepaid_Basic", "Prepaid_Value", "Prepaid_Unlimited",
     "Postpaid_Basic", "Postpaid_Premium", "Postpaid_Family"]
]
onehot_cols = ["gender", "network_type", "occupation", "contract_type"]
ott_passthrough_cols = [f"ott_{ott}" for ott in ["Hotstar", "Netflix", "Prime", "SonyLiv", "Zee5", "Disney"]]

numeric_cols = [
    c for c in X.columns
    if c not in target_encode_cols + ordinal_cols + onehot_cols + ott_passthrough_cols
    and X[c].dtype in ["int64", "float64", "int32", "float32"]
]

print(f"  Target-encode: {len(target_encode_cols)}, Ordinal: {len(ordinal_cols)}, "
      f"OneHot: {len(onehot_cols)}, Numeric (scale): {len(numeric_cols)}, "
      f"OTT passthrough: {len(ott_passthrough_cols)}")

# ── Preprocessing ──────────────────────────────────────────────────────────
preprocessor = ColumnTransformer(
    transformers=[
        ("target_enc", TargetEncoder(smooth="auto"), target_encode_cols),
        ("ordinal", OrdinalEncoder(categories=ordinal_categories), ordinal_cols),
        ("onehot", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="infrequent_if_exist"), onehot_cols),
        ("scaler", StandardScaler(), numeric_cols),
        ("ott_pass", "passthrough", ott_passthrough_cols),
    ],
    remainder="drop",
)

# ── Train/test split ──────────────────────────────────────────────────────
print("Splitting data (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Model 1: Random Forest ────────────────────────────────────────────────
print("\nTraining Random Forest...")
rf_pipe = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_leaf=10,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )),
])
rf_pipe.fit(X_train, y_train)
rf_pred = rf_pipe.predict(X_test)
rf_f1 = f1_score(y_test, rf_pred, average="macro")
print(f"  Random Forest macro F1: {rf_f1:.4f}")
print(classification_report(y_test, rf_pred))

# ── Model 2: XGBoost ──────────────────────────────────────────────────────
print("Training XGBoost...")

# Compute sample weights for class balance
class_counts = y_train.value_counts()
total = len(y_train)
class_weights = {cls: total / (len(class_counts) * cnt) for cls, cnt in class_counts.items()}
sample_weights_train = y_train.map(class_weights).values

# Preprocess for XGBoost (needs numeric input)
X_train_proc = preprocessor.fit_transform(X_train, y_train)
X_test_proc = preprocessor.transform(X_test)

# Encode labels
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
y_train_enc = le.fit_transform(y_train)
y_test_enc = le.transform(y_test)

xgb_clf = XGBClassifier(
    n_estimators=300,
    max_depth=8,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    num_class=3,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
    verbosity=0,
)
xgb_clf.fit(X_train_proc, y_train_enc, sample_weight=sample_weights_train)
xgb_pred_enc = xgb_clf.predict(X_test_proc)
xgb_pred = le.inverse_transform(xgb_pred_enc)
xgb_f1 = f1_score(y_test, xgb_pred, average="macro")
print(f"  XGBoost macro F1: {xgb_f1:.4f}")
print(classification_report(y_test, xgb_pred))

# ── Select winner ─────────────────────────────────────────────────────────
if xgb_f1 >= rf_f1:
    print(f"\n✅ Winner: XGBoost (F1={xgb_f1:.4f})")
    winner = "xgb"
    best_model = xgb_clf
    best_preprocessor = preprocessor
else:
    print(f"\n✅ Winner: Random Forest (F1={rf_f1:.4f})")
    winner = "rf"
    best_model = rf_pipe
    best_preprocessor = None  # embedded in pipeline

# ── Generate predictions on FULL dataset ───────────────────────────────────
print("\nGenerating predictions on full dataset...")

if winner == "xgb":
    X_full_proc = preprocessor.transform(X)
    proba = xgb_clf.predict_proba(X_full_proc)
    pred_enc = xgb_clf.predict(X_full_proc)
    pred_labels = le.inverse_transform(pred_enc)
    class_names = le.classes_
else:
    X_full_proc = rf_pipe.named_steps["preprocessor"].transform(X)
    proba = rf_pipe.predict_proba(X)
    pred_labels = rf_pipe.predict(X)
    class_names = rf_pipe.named_steps["classifier"].classes_

# Build predictions DataFrame
pred_df = pd.DataFrame({
    "customer_id": df["customer_id"],
    "monthly_arpu": df["monthly_arpu"],
    "tenure_months": df["tenure_months"],
    "signup_month": df["signup_month"],
    "predicted_churn_type": pred_labels,
})

# Add probability columns
for i, cls in enumerate(class_names):
    pred_df[f"P({cls})"] = proba[:, i].round(4)

# Derived columns
if "P(Company_Churn)" in pred_df.columns:
    pred_df["revenue_at_risk"] = (pred_df["monthly_arpu"] * pred_df["P(Company_Churn)"]).round(2)
else:
    pred_df["revenue_at_risk"] = 0.0
pred_df["clv"] = (pred_df["monthly_arpu"] * pred_df["tenure_months"]).round(2)

pred_path = os.path.join(SCRIPT_DIR, "churn_predictions.csv")
pred_df.to_csv(pred_path, index=False)
print(f"  Saved predictions: {pred_path}")

# ── SHAP values ────────────────────────────────────────────────────────────
print("\nComputing SHAP values (sampling 5000 rows)...")
shap_sample_idx = np.random.choice(len(X_full_proc), size=5000, replace=False)
X_shap = X_full_proc[shap_sample_idx] if isinstance(X_full_proc, np.ndarray) else X_full_proc[shap_sample_idx]

if winner == "xgb":
    explainer = shap.TreeExplainer(xgb_clf)
else:
    explainer = shap.TreeExplainer(rf_pipe.named_steps["classifier"])

shap_values = explainer.shap_values(X_shap)
shap_values_arr = np.array(shap_values)

# Get feature names from preprocessor
feature_names = preprocessor.get_feature_names_out()

np.save(os.path.join(SCRIPT_DIR, "shap_values.npy"), shap_values_arr)
np.save(os.path.join(SCRIPT_DIR, "shap_feature_names.npy"), feature_names)

# ── Save model ─────────────────────────────────────────────────────────────
model_path = os.path.join(SCRIPT_DIR, "churn_model.pkl")
with open(model_path, "wb") as f:
    pickle.dump({
        "model": best_model,
        "preprocessor": best_preprocessor,
        "label_encoder": le if winner == "xgb" else None,
        "winner": winner,
        "feature_names": list(X.columns),
    }, f)
print(f"  Saved model: {model_path}")

print("\n🎉 Pipeline complete!")
