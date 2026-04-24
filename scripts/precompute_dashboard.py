"""
precompute_dashboard.py
Reads telecom_churn_data.csv and churn_predictions.csv,
computes all dashboard aggregations, writes JSON files to frontend/public/data/.
"""

import os
import json
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "frontend", "public", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_json(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✅ {filename} ({size_kb:.1f} KB)")

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading CSVs...")
main_df = pd.read_csv(os.path.join(SCRIPT_DIR, "telecom_churn_data.csv"))
pred_df = pd.read_csv(os.path.join(SCRIPT_DIR, "churn_predictions.csv"))
print(f"  main_df: {len(main_df):,} rows, pred_df: {len(pred_df):,} rows")

# Merge
merged_df = pred_df.merge(main_df, on="customer_id", suffixes=("_pred", "_main"))

# Resolve column conflicts from merge
if "monthly_arpu_pred" in merged_df.columns:
    merged_df["monthly_arpu"] = merged_df["monthly_arpu_pred"]
    merged_df.drop(columns=["monthly_arpu_pred", "monthly_arpu_main"], inplace=True, errors="ignore")
if "tenure_months_pred" in merged_df.columns:
    merged_df["tenure_months"] = merged_df["tenure_months_pred"]
    merged_df.drop(columns=["tenure_months_pred", "tenure_months_main"], inplace=True, errors="ignore")
if "signup_month_pred" in merged_df.columns:
    merged_df["signup_month"] = merged_df["signup_month_pred"]
    merged_df.drop(columns=["signup_month_pred", "signup_month_main"], inplace=True, errors="ignore")

print(f"  merged_df: {len(merged_df):,} rows")

# ── 1. OVERVIEW JSON ──────────────────────────────────────────────────────
print("\n[1/8] overview.json")

total_customers = len(merged_df)
company_churn_rate = round((merged_df["predicted_churn_type"] == "Company_Churn").mean(), 4)
bundle_switch_rate = round((merged_df["predicted_churn_type"] == "Bundle_Switch").mean(), 4)
total_revenue_at_risk = round(float(merged_df["revenue_at_risk"].sum()), 0)
avg_arpu = round(float(merged_df["monthly_arpu"].mean()), 2)
avg_clv = round(float(merged_df["clv"].mean()), 2)

# Churn type distribution
ct_counts = merged_df["predicted_churn_type"].value_counts(normalize=True)
churn_type_dist = {k: round(v, 4) for k, v in ct_counts.items()}

# ARPU histogram
arpu_counts, arpu_bins = np.histogram(merged_df["monthly_arpu"], bins=30)
arpu_histogram = {
    "bins": [round(float(b), 1) for b in arpu_bins],
    "counts": [int(c) for c in arpu_counts],
}

# Top 10 regions by revenue at risk
region_agg = merged_df.groupby("region").agg(
    revenue_at_risk=("revenue_at_risk", "sum"),
    avg_arpu=("monthly_arpu", "mean"),
    customer_count=("customer_id", "count"),
).reset_index().sort_values("revenue_at_risk", ascending=False).head(10)

top10_regions = [
    {
        "region": row["region"],
        "revenue_at_risk": round(float(row["revenue_at_risk"]), 0),
        "avg_arpu": round(float(row["avg_arpu"]), 2),
        "customer_count": int(row["customer_count"]),
    }
    for _, row in region_agg.iterrows()
]

save_json({
    "total_customers": total_customers,
    "company_churn_rate": company_churn_rate,
    "bundle_switch_rate": bundle_switch_rate,
    "total_revenue_at_risk": total_revenue_at_risk,
    "avg_arpu": avg_arpu,
    "avg_clv": avg_clv,
    "churn_type_distribution": churn_type_dist,
    "arpu_histogram": arpu_histogram,
    "top10_regions_by_revenue_at_risk": top10_regions,
}, "overview.json")

# ── 2. EXPLORER JSON ──────────────────────────────────────────────────────
print("[2/8] explorer.json")

explorer_cols = [
    "customer_id", "region", "plan_tier", "contract_type", "bundle_name",
    "monthly_arpu", "tenure_months", "avg_network_score",
    "support_tickets_6mo", "payment_delays_6mo", "data_usage_ratio",
    "competitor_sim_owned", "monthly_bundle_cost",
]
# churn_type from main_df (actual)
explorer_df = merged_df[explorer_cols + ["churn_type"]].copy()

# Churn rate by contract type
churn_by_contract = {}
for ct in merged_df["contract_type"].unique():
    mask = merged_df["contract_type"] == ct
    rate = (merged_df.loc[mask, "churn_type"] != "Stayed").mean()
    churn_by_contract[ct] = round(float(rate), 4)

# Correlation matrix
corr_features = [
    "monthly_arpu", "tenure_months", "avg_network_score",
    "support_tickets_6mo", "payment_delays_6mo", "data_usage_ratio",
    "competitor_sim_owned", "monthly_bundle_cost",
]
corr_df = merged_df[corr_features].corr()
correlation_matrix = {
    "features": corr_features,
    "values": [[round(float(v), 3) for v in row] for row in corr_df.values],
}

# Convert rows to list of dicts
rows = explorer_df.to_dict(orient="records")
# Round floats in rows
for row in rows:
    for k, v in row.items():
        if isinstance(v, float):
            row[k] = round(v, 3)

save_json({
    "rows": rows,
    "churn_rate_by_contract_type": churn_by_contract,
    "correlation_matrix": correlation_matrix,
}, "explorer.json")

# ── 3. SEGMENTATION JSON ──────────────────────────────────────────────────
print("[3/8] segmentation.json")

# Use P(Company_Churn) as churn_prob
seg_df = pred_df.copy()
if "P(Company_Churn)" in seg_df.columns:
    seg_df["churn_prob"] = seg_df["P(Company_Churn)"]
else:
    seg_df["churn_prob"] = 0.0

# Sample 20K
seg_sample = seg_df.sample(n=min(20000, len(seg_df)), random_state=42)

# Compute medians
median_churn = float(seg_sample["churn_prob"].median())
median_arpu = float(seg_sample["monthly_arpu"].median())

# Assign quadrants
def assign_quadrant(row):
    high_risk = row["churn_prob"] >= median_churn
    high_value = row["monthly_arpu"] >= median_arpu
    if high_risk and high_value:
        return "High_Risk_High_Value"
    elif high_risk and not high_value:
        return "High_Risk_Low_Value"
    elif not high_risk and high_value:
        return "Low_Risk_High_Value"
    else:
        return "Low_Risk_Low_Value"

seg_sample["quadrant"] = seg_sample.apply(assign_quadrant, axis=1)

scatter_points = [
    {
        "customer_id": row["customer_id"],
        "monthly_arpu": round(float(row["monthly_arpu"]), 0),
        "clv": round(float(row["clv"]), 0),
        "tenure_months": int(row["tenure_months"]),
        "churn_prob": round(float(row["churn_prob"]), 4),
        "predicted_churn_type": row["predicted_churn_type"],
        "quadrant": row["quadrant"],
    }
    for _, row in seg_sample.iterrows()
]

quadrant_summary = []
for q in ["High_Risk_High_Value", "High_Risk_Low_Value", "Low_Risk_High_Value", "Low_Risk_Low_Value"]:
    qdf = seg_sample[seg_sample["quadrant"] == q]
    quadrant_summary.append({
        "quadrant": q,
        "count": int(len(qdf)),
        "avg_arpu": round(float(qdf["monthly_arpu"].mean()), 0) if len(qdf) > 0 else 0,
        "avg_clv": round(float(qdf["clv"].mean()), 0) if len(qdf) > 0 else 0,
        "avg_churn_prob": round(float(qdf["churn_prob"].mean()), 4) if len(qdf) > 0 else 0,
        "total_revenue_at_risk": round(float(qdf["revenue_at_risk"].sum()), 0) if len(qdf) > 0 else 0,
    })

save_json({
    "scatter_points": scatter_points,
    "medians": {"churn_prob": round(median_churn, 4), "monthly_arpu": round(median_arpu, 0)},
    "quadrant_summary": quadrant_summary,
}, "segmentation.json")

# ── 4. SEGMENT BLEEDING JSON ──────────────────────────────────────────────
print("[4/8] segment_bleeding.json")

def agg_by(col):
    grp = merged_df.groupby(col).agg(
        customer_count=("customer_id", "count"),
        avg_churn_prob=("revenue_at_risk", lambda x: x.mean()),  # proxy
        avg_arpu=("monthly_arpu", "mean"),
        total_revenue_at_risk=("revenue_at_risk", "sum"),
    ).reset_index().sort_values("total_revenue_at_risk", ascending=False)

    # Recalculate avg_churn_prob properly
    result = []
    for _, row in grp.iterrows():
        mask = merged_df[col] == row[col]
        sub = merged_df[mask]
        if "P(Company_Churn)" in merged_df.columns:
            avg_cp = float(sub["P(Company_Churn)"].mean())
        else:
            avg_cp = 0.0
        result.append({
            "name": str(row[col]),
            "customer_count": int(row["customer_count"]),
            "avg_churn_prob": round(avg_cp, 4),
            "avg_arpu": round(float(row["avg_arpu"]), 2),
            "total_revenue_at_risk": round(float(row["total_revenue_at_risk"]), 0),
        })
    return result

# Need P(Company_Churn) in merged_df
if "P(Company_Churn)" not in merged_df.columns:
    merged_df["P(Company_Churn)"] = pred_df.set_index("customer_id")["P(Company_Churn)"].reindex(merged_df["customer_id"]).values

save_json({
    "by_region": agg_by("region"),
    "by_plan_tier": agg_by("plan_tier"),
    "by_bundle": agg_by("bundle_name"),
    "by_contract_type": agg_by("contract_type"),
}, "segment_bleeding.json")

# ── 5. RETENTION JSON ─────────────────────────────────────────────────────
print("[5/8] retention.json")

ret_df = pred_df.copy()
if "P(Company_Churn)" in ret_df.columns:
    ret_df["churn_prob"] = ret_df["P(Company_Churn)"]
else:
    ret_df["churn_prob"] = 0.0

retention_customers = [
    {
        "customer_id": row["customer_id"],
        "monthly_arpu": round(float(row["monthly_arpu"]), 0),
        "clv": round(float(row["clv"]), 0),
        "churn_prob": round(float(row["churn_prob"]), 4),
        "revenue_at_risk": round(float(row["revenue_at_risk"]), 2),
        "tenure_months": int(row["tenure_months"]),
    }
    for _, row in ret_df.iterrows()
]

save_json({"customers": retention_customers}, "retention.json")

# ── 6. BUNDLE JSON ────────────────────────────────────────────────────────
print("[6/8] bundle.json")

BUNDLE_UPGRADE_MAP = {
    "No_Bundle": {"suggested": "Data_Only", "cost": 49},
    "Data_Only": {"suggested": "Voice_Data", "cost": 79},
    "Voice_Data": {"suggested": "Entertainment_Basic", "cost": 149},
    "Entertainment_Basic": {"suggested": "Entertainment_Premium", "cost": 299},
    "Entertainment_Premium": {"suggested": "OTT_Premium", "cost": 249},
    "OTT_Basic": {"suggested": "OTT_Premium", "cost": 249},
    "OTT_Premium": {"suggested": "Fiber_OTT_Combo", "cost": 899},
    "Fiber_Basic": {"suggested": "Fiber_Premium", "cost": 699},
    "Fiber_Premium": {"suggested": "Fiber_OTT_Combo", "cost": 899},
    "Fiber_OTT_Combo": {"suggested": "Fiber_OTT_Combo", "cost": 899},
}

bun_df = merged_df.copy()
bundle_customers = []
for _, row in bun_df.iterrows():
    bn = row["bundle_name"]
    upgrade = BUNDLE_UPGRADE_MAP.get(bn, {"suggested": bn, "cost": 0})
    current_cost = float(row["monthly_bundle_cost"])
    suggested_cost = upgrade["cost"]
    arpu_delta = max(0, suggested_cost - current_cost)

    bs_prob = float(row.get("P(Bundle_Switch)", 0))
    cc_prob = float(row.get("P(Company_Churn)", 0))
    priority_score = round(bs_prob * 0.6 + (1 - cc_prob) * 0.2 + min(arpu_delta / 500, 1) * 0.2, 4)

    bundle_customers.append({
        "customer_id": row["customer_id"],
        "monthly_arpu": round(float(row["monthly_arpu"]), 0),
        "bundle_name": bn,
        "suggested_bundle": upgrade["suggested"],
        "arpu_delta": round(arpu_delta, 0),
        "bundle_switch_prob": round(bs_prob, 4),
        "company_churn_prob": round(cc_prob, 4),
        "priority_score": priority_score,
        "clv": round(float(row["clv"]), 0),
    })

# Sankey data
all_bundles = list(BUNDLE_UPGRADE_MAP.keys())
# Ensure all bundles are in nodes (source on left, target on right)
source_bundles = sorted(set(b["bundle_name"] for b in bundle_customers))
target_bundles = sorted(set(b["suggested_bundle"] for b in bundle_customers))
all_nodes = list(dict.fromkeys(source_bundles + target_bundles))

# Count flows
from collections import Counter
flow_counts = Counter()
for b in bundle_customers:
    if b["bundle_name"] != b["suggested_bundle"]:
        flow_counts[(b["bundle_name"], b["suggested_bundle"])] += 1

links = []
for (src, tgt), val in flow_counts.most_common():
    if val > 0:
        links.append({
            "source": all_nodes.index(src),
            "target": len(source_bundles) + target_bundles.index(tgt),  # offset for right side
            "value": val,
        })

# Fix nodes for Sankey: left + right
sankey_nodes = source_bundles + [f"{t} " for t in target_bundles]  # space suffix to differentiate

save_json({
    "customers": bundle_customers,
    "sankey": {
        "nodes": sankey_nodes,
        "links": links,
    },
}, "bundle.json")

# ── 7. SEASONAL JSON ──────────────────────────────────────────────────────
print("[7/8] seasonal.json")

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_LABELS = {
    1: "New Year", 3: "End of FY", 6: "Post-IPL",
    10: "Pre-Diwali", 11: "Diwali Peak",
}
HIGH_RISK_MONTHS = {1, 3, 6, 10, 11}

FESTIVAL_CONTEXT = {
    "Oct": "Pre-Diwali: Competitors launch cashback SIM offers. Competitor SIM ownership spikes.",
    "Nov": "Diwali Peak: Highest churn month. Jio/Airtel run aggressive recharge bonuses.",
    "Mar": "End of Financial Year: Corporate plan renewals, budget resets trigger downgrades.",
    "Jan": "New Year: Post-holiday switchers. Prepaid customers most at risk.",
    "Jun": "Post-IPL: OTT bundle churn spike as cricket season ends.",
}

monthly_data = []
for m in range(1, 13):
    mask = merged_df["signup_month"] == m
    sub = merged_df[mask]
    n_cust = len(sub)
    if n_cust == 0:
        continue
    churn_rate = float((sub["churn_type"] != "Stayed").mean())
    rev_at_risk = float(sub["revenue_at_risk"].sum())
    avg_a = float(sub["monthly_arpu"].mean())
    cc_count = int((sub["predicted_churn_type"] == "Company_Churn").sum())
    bs_count = int((sub["predicted_churn_type"] == "Bundle_Switch").sum())

    monthly_data.append({
        "month": m,
        "month_name": MONTH_NAMES[m],
        "label": MONTH_LABELS.get(m, ""),
        "avg_churn_rate": round(churn_rate, 4),
        "total_revenue_at_risk": round(rev_at_risk, 0),
        "avg_arpu": round(avg_a, 2),
        "customer_count": n_cust,
        "company_churn_count": cc_count,
        "bundle_switch_count": bs_count,
        "is_high_risk": m in HIGH_RISK_MONTHS,
    })

# Quarterly
quarterly_data = []
q_map = {
    "Q1": ([1, 2, 3], "Jan–Mar"),
    "Q2": ([4, 5, 6], "Apr–Jun"),
    "Q3": ([7, 8, 9], "Jul–Sep"),
    "Q4": ([10, 11, 12], "Oct–Dec"),
}
q_risk = {"Q1": "Moderate", "Q2": "Low", "Q3": "Low", "Q4": "High"}

for q_name, (months, months_label) in q_map.items():
    mask = merged_df["signup_month"].isin(months)
    sub = merged_df[mask]
    if len(sub) == 0:
        continue
    churn_rate = float((sub["churn_type"] != "Stayed").mean())
    rev_at_risk = float(sub["revenue_at_risk"].sum())
    quarterly_data.append({
        "quarter": q_name,
        "months": months_label,
        "avg_churn_rate": round(churn_rate, 4),
        "total_revenue_at_risk": round(rev_at_risk, 0),
        "risk_level": q_risk[q_name],
    })

save_json({
    "monthly": monthly_data,
    "quarterly": quarterly_data,
    "festival_context": FESTIVAL_CONTEXT,
}, "seasonal.json")

# ── 8. CHATBOT CONTEXT JSON ───────────────────────────────────────────────
print("[8/8] chatbot_context.json")

# Best/worst bundle by churn rate
bundle_churn = merged_df.groupby("bundle_name").apply(
    lambda x: (x["churn_type"] != "Stayed").mean()
).sort_values()
best_bundle = bundle_churn.index[0]
worst_bundle = bundle_churn.index[-1]

# Highest/lowest churn month
month_churn = {}
for m in range(1, 13):
    mask = merged_df["signup_month"] == m
    if mask.sum() > 0:
        month_churn[m] = float((merged_df.loc[mask, "churn_type"] != "Stayed").mean())

highest_month = max(month_churn, key=month_churn.get)
lowest_month = min(month_churn, key=month_churn.get)

# Top risk region
region_risk = merged_df.groupby("region")["revenue_at_risk"].sum()
top_risk_region = region_risk.idxmax()
top_risk_region_rar = float(region_risk.max())

# Q4 vs Q2
q4_rate = float((merged_df[merged_df["signup_month"].isin([10, 11, 12])]["churn_type"] != "Stayed").mean())
q2_rate = float((merged_df[merged_df["signup_month"].isin([4, 5, 6])]["churn_type"] != "Stayed").mean())

save_json({
    "total_customers": total_customers,
    "company_churn_rate": company_churn_rate,
    "total_revenue_at_risk": total_revenue_at_risk,
    "avg_arpu": avg_arpu,
    "top_risk_region": top_risk_region,
    "top_risk_region_revenue_at_risk": round(top_risk_region_rar, 0),
    "highest_churn_month": MONTH_NAMES[highest_month],
    "highest_churn_month_rate": round(month_churn[highest_month], 4),
    "lowest_churn_month": MONTH_NAMES[lowest_month],
    "best_performing_bundle": best_bundle,
    "worst_performing_bundle": worst_bundle,
    "q4_churn_rate": round(q4_rate, 4),
    "q4_vs_q2_delta": round(q4_rate - q2_rate, 4),
}, "chatbot_context.json")

print(f"\n🎉 All JSONs written to {os.path.abspath(OUTPUT_DIR)}")
