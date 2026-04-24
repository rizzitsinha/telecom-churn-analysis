"""
generate_telecom_data.py
Synthesizes 500,000 rows of Indian telecom customer data.
All monetary values in ₹. Output: scripts/telecom_churn_data.csv
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)

N = 500_000
print(f"Generating {N:,} rows of telecom customer data...")

# ── Constants ──────────────────────────────────────────────────────────────
REGIONS = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
    "Tier2_City_1", "Tier2_City_2", "Tier2_City_3", "Tier2_City_4",
]
METRO_CITIES = {"Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"}

GENDERS = ["Male", "Female"]
OCCUPATIONS = ["Student", "Salaried", "Self_Employed", "Business", "Retired", "Homemaker"]

PLAN_TIERS = [
    "Prepaid_Basic", "Prepaid_Value", "Prepaid_Unlimited",
    "Postpaid_Basic", "Postpaid_Premium", "Postpaid_Family",
]
CONTRACT_TYPES = ["Monthly", "Quarterly", "Annual", "2_Year"]
NETWORK_TYPES = ["2G", "3G", "4G", "5G"]

BUNDLE_NAMES = [
    "No_Bundle", "Data_Only", "Voice_Data",
    "Entertainment_Basic", "Entertainment_Premium",
    "OTT_Basic", "OTT_Premium",
    "Fiber_Basic", "Fiber_Premium", "Fiber_OTT_Combo",
]
OTT_LIST = ["Hotstar", "Netflix", "Prime", "SonyLiv", "Zee5", "Disney"]

SEASONAL_MULTIPLIERS = {
    1: 1.20,   # New Year
    3: 1.30,   # End of FY
    6: 1.15,   # Post-IPL
    10: 1.40,  # Pre-Diwali
    11: 1.60,  # Diwali peak
}

# ── Demographics ───────────────────────────────────────────────────────────
print("  [1/10] Demographics...")
customer_id = np.array([f"C{str(i).zfill(6)}" for i in range(1, N + 1)])
region = np.random.choice(REGIONS, N)
is_metro = np.array([1 if r in METRO_CITIES else 0 for r in region])
age = np.random.randint(18, 75, N)
gender = np.random.choice(GENDERS, N)
occupation = np.random.choice(OCCUPATIONS, N, p=[0.15, 0.35, 0.15, 0.15, 0.10, 0.10])

# ── Plan & Contract ───────────────────────────────────────────────────────
print("  [2/10] Plan & Contract...")
plan_tier = np.random.choice(PLAN_TIERS, N, p=[0.20, 0.18, 0.17, 0.20, 0.15, 0.10])
contract_type = np.random.choice(CONTRACT_TYPES, N, p=[0.40, 0.25, 0.25, 0.10])

contract_length_map = {"Monthly": 1, "Quarterly": 3, "Annual": 12, "2_Year": 24}
contract_length_months = np.array([contract_length_map[c] for c in contract_type])

tenure_months = np.random.exponential(scale=24, size=N).astype(int).clip(1, 120)
network_type = np.random.choice(NETWORK_TYPES, N, p=[0.05, 0.15, 0.55, 0.25])

# ── Bundle ─────────────────────────────────────────────────────────────────
print("  [3/10] Bundle...")
bundle_name = np.random.choice(BUNDLE_NAMES, N,
    p=[0.15, 0.10, 0.12, 0.10, 0.08, 0.12, 0.08, 0.10, 0.08, 0.07])

# OTT platforms based on bundle
ott_platforms_list = []
num_ott_platforms_arr = []
for b in bundle_name:
    if b in ("No_Bundle", "Data_Only", "Voice_Data"):
        n_ott = np.random.choice([0, 1], p=[0.7, 0.3])
    elif b in ("Entertainment_Basic", "OTT_Basic", "Fiber_Basic"):
        n_ott = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
    else:
        n_ott = np.random.choice([2, 3, 4, 5, 6], p=[0.15, 0.25, 0.30, 0.20, 0.10])
    if n_ott == 0:
        ott_platforms_list.append("")
    else:
        chosen = np.random.choice(OTT_LIST, size=min(n_ott, len(OTT_LIST)), replace=False)
        ott_platforms_list.append("|".join(chosen))
    num_ott_platforms_arr.append(n_ott)

ott_platforms = np.array(ott_platforms_list)
num_ott_platforms = np.array(num_ott_platforms_arr)

# Monthly bundle cost correlated with plan tier and bundle
plan_tier_base_cost = {
    "Prepaid_Basic": 99, "Prepaid_Value": 199, "Prepaid_Unlimited": 399,
    "Postpaid_Basic": 299, "Postpaid_Premium": 599, "Postpaid_Family": 799,
}
bundle_addon_cost = {
    "No_Bundle": 0, "Data_Only": 49, "Voice_Data": 79,
    "Entertainment_Basic": 149, "Entertainment_Premium": 299,
    "OTT_Basic": 99, "OTT_Premium": 249,
    "Fiber_Basic": 399, "Fiber_Premium": 699, "Fiber_OTT_Combo": 899,
}
monthly_bundle_cost = np.array([
    bundle_addon_cost[b] + np.random.randint(-20, 20)
    for b in bundle_name
]).clip(0)

bundle_switches_6mo = np.random.poisson(0.5, N).clip(0, 5)

# ── Usage ──────────────────────────────────────────────────────────────────
print("  [4/10] Usage...")
daily_data_limit_gb = np.random.choice([0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0], N,
    p=[0.05, 0.15, 0.20, 0.25, 0.20, 0.10, 0.05])
avg_daily_data_used_gb = (daily_data_limit_gb * np.random.uniform(0.3, 1.3, N)).round(2)
data_usage_ratio = (avg_daily_data_used_gb / daily_data_limit_gb).round(3)
total_data_used_gb_mo = (avg_daily_data_used_gb * 30).round(1)
data_overuse_days_mo = np.where(
    data_usage_ratio > 1.0,
    np.random.randint(1, 20, N),
    0
)

monthly_call_minutes = np.random.lognormal(mean=5.5, sigma=0.8, size=N).astype(int).clip(10, 3000)
monthly_sms_count = np.random.exponential(scale=30, size=N).astype(int).clip(0, 500)
roaming_calls_mo = np.random.poisson(2, N).clip(0, 50)
international_calls_mo = np.random.poisson(0.5, N).clip(0, 20)

# ── Financial ──────────────────────────────────────────────────────────────
print("  [5/10] Financial...")
base_arpu = np.array([plan_tier_base_cost[p] for p in plan_tier], dtype=float)
monthly_arpu = (base_arpu + monthly_bundle_cost + np.random.normal(0, 50, N)).clip(50, 2500).round(0)
total_revenue_ltv = (monthly_arpu * tenure_months).round(0)
payment_delays_6mo = np.random.poisson(1.0, N).clip(0, 10)
recharge_frequency = np.random.choice(
    ["Weekly", "Bi-Weekly", "Monthly", "Quarterly", "Irregular"], N,
    p=[0.10, 0.15, 0.40, 0.20, 0.15]
)
days_since_last_recharge = np.random.exponential(scale=15, size=N).astype(int).clip(0, 180)

# ── Network & Support ─────────────────────────────────────────────────────
print("  [6/10] Network & Support...")
avg_network_score = np.random.normal(6.5, 1.8, N).clip(1, 10).round(1)
outage_incidents_mo = np.random.poisson(0.8, N).clip(0, 10)
support_tickets_6mo = np.random.poisson(2.0, N).clip(0, 20)
complaint_resolved = np.random.choice(["Yes", "No", "Pending"], N, p=[0.60, 0.15, 0.25])

# ── Behavioral ─────────────────────────────────────────────────────────────
print("  [7/10] Behavioral...")
app_logins_per_week = np.random.poisson(4, N).clip(0, 30)
competitor_sim_owned = np.random.choice([0, 1], N, p=[0.65, 0.35])
upgrade_offers_shown = np.random.poisson(3, N).clip(0, 15)
upgrade_offers_accepted = np.minimum(
    np.random.poisson(0.5, N).clip(0, 5), upgrade_offers_shown
)
retention_offers_6mo = np.random.poisson(1.5, N).clip(0, 8)
retention_offer_accepted = np.random.choice([0, 1], N, p=[0.70, 0.30])
loyalty_points_balance = np.random.exponential(scale=500, size=N).astype(int).clip(0, 10000)

# ── Seasonal columns ──────────────────────────────────────────────────────
print("  [8/10] Seasonal columns...")
signup_month = np.random.randint(1, 13, N)
seasonal_churn_multiplier = np.array([
    SEASONAL_MULTIPLIERS.get(m, 1.0) for m in signup_month
])

# ── Churn target ───────────────────────────────────────────────────────────
print("  [9/10] Computing churn target...")

# Build logistic churn score from features
plan_tier_idx = np.array([PLAN_TIERS.index(p) for p in plan_tier])
contract_type_risk = {"Monthly": 0.4, "Quarterly": 0.2, "Annual": -0.2, "2_Year": -0.5}
contract_risk = np.array([contract_type_risk[c] for c in contract_type])

logit = (
    0.0
    + 1.5 * (payment_delays_6mo / 10)
    + 1.8 * (support_tickets_6mo / 20)
    + 0.8 * competitor_sim_owned
    - 1.5 * (tenure_months / 120)
    - 1.2 * (avg_network_score / 10)
    + 0.6 * (data_usage_ratio - 1.0).clip(0)
    + 0.8 * (days_since_last_recharge / 180)
    - 0.6 * (loyalty_points_balance / 10000)
    + 0.7 * contract_risk
    - 0.5 * (plan_tier_idx / 5)
    + 0.5 * (bundle_switches_6mo / 5)
    - 0.4 * (retention_offer_accepted)
    + 0.6 * (outage_incidents_mo / 10)
    - 0.4 * (num_ott_platforms / 6)
    + np.random.normal(0, 0.5, N)  # noise
)

# Apply seasonal multiplier BEFORE sigmoid
logit_seasonal = logit * seasonal_churn_multiplier
churn_probability_score = 1 / (1 + np.exp(-logit_seasonal))
churn_probability_score = churn_probability_score.round(4)

churn = (churn_probability_score >= 0.42).astype(int)

# Churn type: ~70% Stayed, ~15% Bundle_Switch, ~15% Company_Churn
churn_type = np.where(churn == 0, "Stayed", "").astype(object)
churned_mask = churn == 1
n_churned = churned_mask.sum()
churn_sub = np.random.choice(
    ["Bundle_Switch", "Company_Churn"], n_churned, p=[0.50, 0.50]
)
churn_type[churned_mask] = churn_sub

# ── Assemble DataFrame ────────────────────────────────────────────────────
print("  [10/10] Assembling DataFrame and saving CSV...")

df = pd.DataFrame({
    "customer_id": customer_id,
    "region": region,
    "age": age,
    "gender": gender,
    "occupation": occupation,
    "is_metro": is_metro,
    "plan_tier": plan_tier,
    "contract_type": contract_type,
    "contract_length_months": contract_length_months,
    "tenure_months": tenure_months,
    "network_type": network_type,
    "bundle_name": bundle_name,
    "ott_platforms": ott_platforms,
    "num_ott_platforms": num_ott_platforms,
    "monthly_bundle_cost": monthly_bundle_cost,
    "bundle_switches_6mo": bundle_switches_6mo,
    "daily_data_limit_gb": daily_data_limit_gb,
    "avg_daily_data_used_gb": avg_daily_data_used_gb,
    "data_usage_ratio": data_usage_ratio,
    "total_data_used_gb_mo": total_data_used_gb_mo,
    "data_overuse_days_mo": data_overuse_days_mo,
    "monthly_call_minutes": monthly_call_minutes,
    "monthly_sms_count": monthly_sms_count,
    "roaming_calls_mo": roaming_calls_mo,
    "international_calls_mo": international_calls_mo,
    "monthly_arpu": monthly_arpu,
    "total_revenue_ltv": total_revenue_ltv,
    "payment_delays_6mo": payment_delays_6mo,
    "recharge_frequency": recharge_frequency,
    "days_since_last_recharge": days_since_last_recharge,
    "avg_network_score": avg_network_score,
    "outage_incidents_mo": outage_incidents_mo,
    "support_tickets_6mo": support_tickets_6mo,
    "complaint_resolved": complaint_resolved,
    "app_logins_per_week": app_logins_per_week,
    "competitor_sim_owned": competitor_sim_owned,
    "upgrade_offers_shown": upgrade_offers_shown,
    "upgrade_offers_accepted": upgrade_offers_accepted,
    "retention_offers_6mo": retention_offers_6mo,
    "retention_offer_accepted": retention_offer_accepted,
    "loyalty_points_balance": loyalty_points_balance,
    "signup_month": signup_month,
    "seasonal_churn_multiplier": seasonal_churn_multiplier,
    "churn": churn,
    "churn_type": churn_type,
    "churn_probability_score": churn_probability_score,
})

output_path = os.path.join(os.path.dirname(__file__), "telecom_churn_data.csv")
df.to_csv(output_path, index=False)

print(f"\n✅ Generated {len(df):,} rows with {len(df.columns)} columns")
print(f"   Saved to: {output_path}")
print(f"\n   Churn distribution:")
print(df["churn_type"].value_counts().to_string())
print(f"\n   Seasonal multiplier distribution:")
print(df["seasonal_churn_multiplier"].value_counts().sort_index().to_string())
