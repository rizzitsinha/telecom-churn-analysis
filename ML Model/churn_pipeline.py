# Requires: pip install shap  (for SHAP analysis in Step 10a)
"""
Telecom Customer Churn Prediction Pipeline
===========================================
Target: churn_type (multiclass — Stayed, Bundle_Switch, Company_Churn)
Models: Random Forest, XGBoost
Output: churn_model.pkl  (better model)
        churn_predictions.csv (test-set predictions + revenue_at_risk + clv)
        shap_values.npy, shap_explainer.pkl, shap_feature_names.npy,
        shap_summary_plot.png  (SHAP analysis artefacts)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import (
    OrdinalEncoder,
    OneHotEncoder,
    StandardScaler,
    FunctionTransformer,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

# Try importing TargetEncoder (scikit-learn >= 1.3)
from sklearn.preprocessing import TargetEncoder

# ──────────────────────────────────────────────
# 1.  LOAD DATA
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 1 — Loading data …")
print("=" * 70)

df = pd.read_csv("telecom_churn_data.csv")
print(f"  Shape : {df.shape}")
print(f"  Target distribution:\n{df['churn_type'].value_counts()}\n")

# ──────────────────────────────────────────────
# 2.  DROP COLUMNS
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 2 — Dropping columns: customer_id, churn, churn_probability_score")
print("=" * 70)

# Keep customer_id, monthly_arpu, tenure_months & contract_length_months aside for later use
id_cols = df[["customer_id", "monthly_arpu", "tenure_months", "contract_length_months"]].copy()

drop_cols = ["customer_id", "churn", "churn_probability_score"]
df.drop(columns=drop_cols, inplace=True)
print(f"  Shape after drop: {df.shape}\n")

# ──────────────────────────────────────────────
# 3.  FEATURE ENGINEERING
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 3 — Feature engineering …")
print("=" * 70)

# data_usage_ratio — already exists, skip
print("  • data_usage_ratio — already present, skipping")

# is_irregular_recharge — binary flag
df["is_irregular_recharge"] = (df["recharge_frequency"] == "Irregular").astype(int)
print("  • is_irregular_recharge — created")

# arpu_per_tenure
df["arpu_per_tenure"] = df["monthly_arpu"] / (df["tenure_months"] + 1)
print("  • arpu_per_tenure — created")

# support_per_month
df["support_per_month"] = df["support_tickets_6mo"] / 6
print("  • support_per_month — created")

print(f"  Shape after FE: {df.shape}\n")

# ──────────────────────────────────────────────
# 4.  HANDLE ott_platforms (multi-label → binary cols)
# ──────────────────────────────────────────────
# ott_platforms contains pipe-separated values like "Hotstar|SonyLIV".
# We explode them into binary columns BEFORE sklearn so OneHot isn't
# applied to hundreds of pipe-separated combos.
print("=" * 70)
print("STEP 4 — Exploding ott_platforms into binary columns …")
print("=" * 70)

df["ott_platforms"] = df["ott_platforms"].fillna("None")
unique_platforms = set()
for val in df["ott_platforms"].unique():
    for p in val.split("|"):
        unique_platforms.add(p.strip())

for platform in sorted(unique_platforms):
    col_name = f"ott_{platform}"
    df[col_name] = df["ott_platforms"].apply(
        lambda x, p=platform: int(p in x.split("|"))
    )
    print(f"  • {col_name}")

# Drop original ott_platforms column — we've replaced it
df.drop(columns=["ott_platforms"], inplace=True)

# Also handle NA/NaN values in complaint_resolved for cleaner encoding
df["complaint_resolved"] = df["complaint_resolved"].fillna("N/A")
df["recharge_frequency"] = df["recharge_frequency"].fillna("N/A")

print(f"  Shape after ott explosion: {df.shape}\n")

# ──────────────────────────────────────────────
# 5.  SEPARATE X / y & TRAIN-TEST SPLIT
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 5 — Train / test split (80 / 20, stratified) …")
print("=" * 70)

TARGET = "churn_type"
y = df[TARGET]
X = df.drop(columns=[TARGET])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Align id_cols with test indices for later result reconstruction
id_test = id_cols.loc[X_test.index].reset_index(drop=True)

print(f"  Train : {X_train.shape}  |  Test : {X_test.shape}\n")

# ──────────────────────────────────────────────
# 6.  BUILD COLUMN TRANSFORMER
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 6 — Building ColumnTransformer …")
print("=" * 70)

# --- Column lists ---
target_enc_cols = ["region", "bundle_name", "complaint_resolved", "recharge_frequency"]

ordinal_col = ["plan_tier"]
plan_tier_order = [
    "Prepaid_Basic",
    "Prepaid_Mid",
    "Prepaid_Premium",
    "Postpaid_Basic",
    "Postpaid_Premium",
    "Postpaid_Family",
]
# Student_Pack exists in data but not in the user's ordered list.
# Append it at position 0 (lowest tier) so OrdinalEncoder doesn't crash.
plan_tier_full_order = ["Student_Pack"] + plan_tier_order

onehot_cols = ["gender", "network_type", "occupation", "contract_type"]
# NOTE: ott_platforms already exploded into binary cols above,
# so we do NOT include "ott_platforms" here.

# Gather ott binary columns created above
ott_binary_cols = [c for c in X.columns if c.startswith("ott_")]

# All remaining numeric columns
all_specified = set(target_enc_cols + ordinal_col + onehot_cols + ott_binary_cols)
numeric_cols = [
    c for c in X.columns
    if c not in all_specified and pd.api.types.is_numeric_dtype(X[c])
]

print(f"  TargetEncoder cols  : {target_enc_cols}")
print(f"  OrdinalEncoder cols : {ordinal_col}")
print(f"  OneHotEncoder cols  : {onehot_cols}")
print(f"  OTT binary cols     : {ott_binary_cols}")
print(f"  StandardScaler cols : {len(numeric_cols)} numeric features")

preprocessor = ColumnTransformer(
    transformers=[
        (
            "target_enc",
            TargetEncoder(smooth="auto", target_type="multiclass"),
            target_enc_cols,
        ),
        (
            "ordinal_enc",
            OrdinalEncoder(
                categories=[plan_tier_full_order],
                handle_unknown="use_encoded_value",
                unknown_value=-1,
            ),
            ordinal_col,
        ),
        (
            "onehot_enc",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            onehot_cols,
        ),
        (
            "ott_pass",
            "passthrough",
            ott_binary_cols,
        ),
        (
            "scaler",
            StandardScaler(),
            numeric_cols,
        ),
    ],
    remainder="drop",
    verbose_feature_names_out=False,
)

print("  ColumnTransformer built ✓\n")

# ──────────────────────────────────────────────
# 7.  BUILD & TRAIN PIPELINES
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 7 — Training models …")
print("=" * 70)

'''
# --- 7a. Random Forest ---
print("\n  ▸ Random Forest …")
rf_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )),
])
rf_pipeline.fit(X_train, y_train)
print("    trained ✓")
'''
# --- 7b. XGBoost ---
print("  ▸ XGBoost …")

# Encode target labels for XGBoost (needs ints)
from sklearn.preprocessing import LabelEncoder

le = LabelEncoder()
le.fit(y)  # fit on full y to guarantee consistent mapping
y_train_enc = le.transform(y_train)
y_test_enc = le.transform(y_test)

xgb_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        n_estimators=300,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        eval_metric="mlogloss",
        verbosity=0,
    )),
])

sample_weights = compute_sample_weight(class_weight="balanced", y=y_train_enc)
xgb_pipeline.fit(X_train, y_train_enc, classifier__sample_weight=sample_weights)
print("    trained ✓\n")

# ──────────────────────────────────────────────
# 8.  EVALUATION
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 8 — Evaluation on test set")
print("=" * 70)

class_names = le.classes_  # ['Bundle_Switch', 'Company_Churn', 'Stayed']
'''
# --- Random Forest ---
rf_preds = rf_pipeline.predict(X_test)
rf_proba = rf_pipeline.predict_proba(X_test)

print("\n┌──────────────────────────────────────────┐")
print("│        RANDOM FOREST — Report            │")
print("└──────────────────────────────────────────┘")
print(classification_report(y_test, rf_preds, target_names=class_names))

print("Confusion Matrix (RF):")
rf_cm = confusion_matrix(y_test, rf_preds, labels=class_names)
print(pd.DataFrame(rf_cm, index=class_names, columns=class_names))

rf_accuracy = (rf_preds == y_test).mean()
rf_f1 = f1_score(y_test, rf_preds, average="macro", labels=class_names)
print(f"\nRF Accuracy: {rf_accuracy:.4f}")
print(f"RF Macro F1: {rf_f1:.4f}")
'''
# --- XGBoost ---
xgb_preds_enc = xgb_pipeline.predict(X_test)
xgb_preds = le.inverse_transform(xgb_preds_enc)
xgb_proba = xgb_pipeline.predict_proba(X_test)

print("\n┌──────────────────────────────────────────┐")
print("│           XGBOOST — Report               │")
print("└──────────────────────────────────────────┘")
print(classification_report(y_test, xgb_preds, target_names=class_names))

print("Confusion Matrix (XGB):")
xgb_cm = confusion_matrix(y_test, xgb_preds, labels=class_names)
print(pd.DataFrame(xgb_cm, index=class_names, columns=class_names))

xgb_accuracy = (xgb_preds == y_test.values).mean()
xgb_f1 = f1_score(y_test, xgb_preds, average="macro", labels=class_names)
print(f"\nXGB Accuracy: {xgb_accuracy:.4f}")
print(f"XGB Macro F1: {xgb_f1:.4f}")

# ──────────────────────────────────────────────
# 9.  SAVE BETTER MODEL
# ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 9 — Saving better model as churn_model.pkl …")
print("=" * 70)

# if xgb_f1 >= rf_f1:
best_name = "XGBoost"
best_pipeline = xgb_pipeline
best_proba = xgb_proba
best_preds = xgb_preds
best_f1 = xgb_f1
# else:
#     best_name = "Random Forest"
#     best_pipeline = rf_pipeline
#     best_proba = rf_proba
#     best_preds = rf_preds
#     best_f1 = rf_f1

joblib.dump(best_pipeline, "churn_model.pkl")
print(f"  Best model: {best_name} (macro F1={best_f1:.4f})")
print("  Saved → churn_model.pkl ✓\n")

# ──────────────────────────────────────────────
# 10a. SHAP ANALYSIS & EXPORT
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 10a — SHAP analysis & export …")
print("=" * 70)

import shap

# Sample 5000 rows from X_test (SHAP is slow on 100k rows)
X_shap_sample = X_test.sample(5000, random_state=42)

# Extract preprocessor and transform the sample
preprocessor_fitted = best_pipeline.named_steps["preprocessor"]
X_shap_transformed = preprocessor_fitted.transform(X_shap_sample)

# Build SHAP TreeExplainer on the underlying classifier
print("  Computing SHAP values (this may take a few minutes) …")

explainer = shap.TreeExplainer(best_pipeline.named_steps["classifier"])
shap_values = explainer.shap_values(X_shap_transformed)

# shap_values is a list of arrays for multiclass: [array_class0, array_class1, array_class2]
# Stack into (n_classes, n_samples, n_features)

shap_values_array = np.array(shap_values)

print(f"  SHAP values shape: {shap_values_array.shape}")

# Save SHAP values & explainer
np.save("shap_values.npy", shap_values_array)
joblib.dump(explainer, "shap_explainer.pkl")

# Get and save feature names from the fitted ColumnTransformer
feature_names = preprocessor_fitted.get_feature_names_out()
np.save("shap_feature_names.npy", np.array(feature_names))
print(f"  Feature names: {len(feature_names)} features")

# Generate SHAP summary plot for Company_Churn class (index 2 in sorted class order)
# Class order from LabelEncoder: ['Bundle_Switch', 'Company_Churn', 'Stayed']
company_churn_class_idx = list(class_names).index("Company_Churn") if "Company_Churn" in class_names else 1
shap.summary_plot(
    shap_values[company_churn_class_idx],
    X_shap_transformed,
    feature_names=feature_names,
    show=False,
    max_display=15,
)
plt.savefig("shap_summary_plot.png", bbox_inches="tight", dpi=150, facecolor="white")
plt.close()

print("  Saved → shap_values.npy")
print("  Saved → shap_explainer.pkl")
print("  Saved → shap_feature_names.npy")
print("  Saved → shap_summary_plot.png ✓\n")

# ──────────────────────────────────────────────
# 10b. BUILD RESULTS DATAFRAME & SAVE CSV
# ──────────────────────────────────────────────
print("=" * 70)
print("STEP 10b — Building predictions CSV …")
print("=" * 70)

# Map class order from the best model
# For RF, classes_ is in the pipeline; for XGB we used LabelEncoder
if best_name == "Random Forest":
    prob_classes = rf_pipeline.named_steps["classifier"].classes_
else:
    prob_classes = le.classes_

results = pd.DataFrame({
    "customer_id": id_test["customer_id"].values,
    "monthly_arpu": id_test["monthly_arpu"].values,
    "predicted_churn_type": best_preds,
})

# expected_remaining_tenure = contract_length_months - (tenure_months % contract_length_months)
tenure_arr = id_test["tenure_months"].values
contract_arr = id_test["contract_length_months"].values
tenure_in_current_cycle = tenure_arr % contract_arr
expected_remaining_tenure = contract_arr - tenure_in_current_cycle
results["expected_remaining_tenure"] = expected_remaining_tenure

# Add probability columns in the requested order
for i, cls in enumerate(prob_classes):
    results[f"P({cls})"] = best_proba[:, i]

# revenue_at_risk = monthly_arpu × P(Company_Churn)
company_churn_idx = list(prob_classes).index("Company_Churn")
results["revenue_at_risk"] = (
    results["monthly_arpu"] * best_proba[:, company_churn_idx]
)

# clv = monthly_arpu × expected_remaining_tenure
results["clv"] = results["monthly_arpu"] * results["expected_remaining_tenure"]

# retention_cost_breakeven = P(Company_Churn) × clv
results["retention_cost_breakeven"] = best_proba[:, company_churn_idx] * results["clv"]

results.to_csv("churn_predictions.csv", index=False)
print(f"  Rows: {len(results)}")
print(f"  Columns: {list(results.columns)}")
print("  Saved → churn_predictions.csv ✓")

print("\n" + "=" * 70)
print("PIPELINE COMPLETE ✅")
print("=" * 70)
print(f"  • Model saved     : churn_model.pkl ({best_name}, macro F1={best_f1:.4f})")
print(f"  • Predictions     : churn_predictions.csv ({len(results)} rows)")
print(f"  • SHAP artefacts  : shap_values.npy, shap_explainer.pkl,")
print(f"                      shap_feature_names.npy, shap_summary_plot.png")
print("=" * 70)
