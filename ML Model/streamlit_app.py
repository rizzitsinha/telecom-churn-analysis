import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Telecom Churn Analytics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #e0e0ff;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #e0e0ff !important;
    }

    /* Metric card styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea11 0%, #764ba211 100%);
        border: 1px solid #667eea33;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.08);
    }
    div[data-testid="stMetric"] label {
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }

    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Hide default menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #888;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Data Loading
# ──────────────────────────────────────────────────────────────
@st.cache_data
def load_main_data():
    df = pd.read_csv("telecom_churn_data.csv")
    return df


@st.cache_data
def load_predictions():
    df = pd.read_csv("churn_predictions.csv")
    return df


with st.spinner("Loading datasets…"):
    main_df = load_main_data()
    pred_df = load_predictions()


# ──────────────────────────────────────────────────────────────
# Plotly theme helper
# ──────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13),
    margin=dict(l=40, r=30, t=50, b=40),
)

COLOR_PALETTE = ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b",
                 "#fa709a", "#fee140", "#a18cd1", "#fbc2eb", "#ff9a9e"]


def format_inr(value):
    """Format value in Indian Rupee Crores or Lakhs."""
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:.2f}Cr"
    elif abs(value) >= 1e5:
        return f"₹{value / 1e5:.2f}L"
    else:
        return f"₹{value:,.0f}"


def format_inr_plain(value):
    """Format value as ₹XX,XXX."""
    return f"₹{value:,.0f}"


# ──────────────────────────────────────────────────────────────
# Sidebar Navigation
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Telecom Churn")
    st.markdown("##### Analytics Platform")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        [
            "📊 Overview Dashboard",
            "🔍 Data Explorer",
            "🤖 Model Performance & SHAP",
            "💡 AI Strategic Recommendations",
            "🎯 Customer Segmentation",
            "🩸 Segment Bleeding Analysis",
            "🛡️ Retention Planner",
            "📦 Bundle Opportunity Analysis",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(f"Main dataset: **{len(main_df):,}** rows")
    st.caption(f"Predictions: **{len(pred_df):,}** rows")


# ══════════════════════════════════════════════════════════════
# PAGE 1 — Overview Dashboard
# ══════════════════════════════════════════════════════════════
if page == "📊 Overview Dashboard":
    st.markdown('<p class="main-header">Overview Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Key performance indicators & high-level churn insights</p>',
                unsafe_allow_html=True)

    # ── KPI Row ──
    k1, k2, k3, k4, k5 = st.columns(5)
    total_customers = len(main_df)
    churn_rate = main_df["churn"].mean() * 100
    total_rev_risk = pred_df["revenue_at_risk"].sum()
    avg_arpu = main_df["monthly_arpu"].mean()
    avg_clv = pred_df["clv"].mean()

    k1.metric("Total Customers", f"{total_customers:,}")
    k2.metric("Company Churn Rate", f"{churn_rate:.2f}%")
    k3.metric("Revenue at Risk", format_inr(total_rev_risk))
    k4.metric("Avg ARPU", f"₹{avg_arpu:,.0f}")
    k5.metric("Avg CLV", f"₹{avg_clv:,.0f}")

    st.markdown("")

    # ── Row 2: Donut + ARPU Distribution ──
    col_a, col_b = st.columns(2)

    with col_a:
        churn_dist = main_df["churn_type"].value_counts().reset_index()
        churn_dist.columns = ["Churn Type", "Count"]
        fig_donut = px.pie(
            churn_dist, names="Churn Type", values="Count", hole=0.5,
            title="Churn Type Distribution",
            color_discrete_sequence=COLOR_PALETTE,
        )
        fig_donut.update_layout(**PLOTLY_LAYOUT)
        fig_donut.update_traces(textinfo="percent+label", textfont_size=12)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_b:
        fig_arpu = px.histogram(
            main_df, x="monthly_arpu", nbins=50,
            title="ARPU Distribution",
            labels={"monthly_arpu": "Monthly ARPU (₹)", "count": "Customer Count"},
            color_discrete_sequence=["#667eea"],
        )
        fig_arpu.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_arpu, use_container_width=True)

    # ── Row 3: Top Regions by Revenue at Risk ──
    with st.spinner("Computing regional revenue at risk…"):
        merged_region = pred_df.merge(
            main_df[["customer_id", "region"]], on="customer_id", how="left"
        ).dropna(subset=["region"])
        region_risk = (
            merged_region.groupby("region")["revenue_at_risk"]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        region_risk.columns = ["Region", "Revenue at Risk"]

    fig_region = px.bar(
        region_risk, y="Region", x="Revenue at Risk",
        orientation="h",
        title="Top 10 Regions by Revenue at Risk",
        labels={"Revenue at Risk": "Revenue at Risk (₹)"},
        color="Revenue at Risk",
        color_continuous_scale="Reds",
    )
    fig_region.update_layout(**PLOTLY_LAYOUT, yaxis=dict(autorange="reversed"))
    fig_region.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_region, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# PAGE 2 — Data Explorer
# ══════════════════════════════════════════════════════════════
elif page == "🔍 Data Explorer":
    st.markdown('<p class="main-header">Data Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Filter, explore & visualise the raw telecom dataset</p>',
                unsafe_allow_html=True)

    # ── Sidebar filters ──
    with st.sidebar:
        st.markdown("### 🔎 Filters")
        sel_region = st.multiselect("Region", sorted(main_df["region"].unique()))
        sel_plan = st.multiselect("Plan Tier", sorted(main_df["plan_tier"].unique()))
        sel_contract = st.multiselect("Contract Type", sorted(main_df["contract_type"].unique()))
        sel_bundle = st.multiselect("Bundle Name", sorted(main_df["bundle_name"].unique()))

    filtered = main_df.copy()
    if sel_region:
        filtered = filtered[filtered["region"].isin(sel_region)]
    if sel_plan:
        filtered = filtered[filtered["plan_tier"].isin(sel_plan)]
    if sel_contract:
        filtered = filtered[filtered["contract_type"].isin(sel_contract)]
    if sel_bundle:
        filtered = filtered[filtered["bundle_name"].isin(sel_bundle)]

    st.info(f"Showing **{len(filtered):,}** rows after filters (total: {len(main_df):,})")

    # ── Row 1: Data preview ──
    st.dataframe(filtered.head(10), use_container_width=True, height=400)

    # ── Row 2: Histogram + Churn by Contract ──
    c1, c2 = st.columns(2)
    with c1:
        numeric_cols = filtered.select_dtypes(include="number").columns.tolist()
        chosen_col = st.selectbox("Select numeric column for histogram", numeric_cols,
                                  index=numeric_cols.index("monthly_arpu") if "monthly_arpu" in numeric_cols else 0)
        fig_hist = px.histogram(
            filtered, x=chosen_col, nbins=50,
            title=f"Distribution of {chosen_col}",
            labels={chosen_col: chosen_col, "count": "Count"},
            color_discrete_sequence=["#764ba2"],
        )
        fig_hist.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        churn_contract = (
            filtered.groupby("contract_type")["churn"].mean().reset_index()
        )
        churn_contract.columns = ["Contract Type", "Churn Rate"]
        fig_cc = px.bar(
            churn_contract, x="Contract Type", y="Churn Rate",
            title="Churn Rate by Contract Type",
            labels={"Churn Rate": "Churn Rate (proportion)"},
            color="Churn Rate",
            color_continuous_scale="RdYlGn_r",
        )
        fig_cc.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
        st.plotly_chart(fig_cc, use_container_width=True)

    # ── Row 3: Correlation Heatmap ──
    st.subheader("Correlation Heatmap")
    corr_cols = [
        "monthly_arpu", "tenure_months", "data_usage_ratio", "support_tickets_6mo",
        "avg_network_score", "payment_delays_6mo", "app_logins_per_week",
        "loyalty_points_balance", "bundle_switches_6mo", "monthly_call_minutes",
    ]
    corr_cols = [c for c in corr_cols if c in filtered.columns]
    corr_matrix = filtered[corr_cols].corr()

    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns.tolist(),
        y=corr_matrix.columns.tolist(),
        colorscale="RdBu_r",
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=10),
    ))
    fig_corr.update_layout(
        title="Feature Correlation Matrix",
        height=600,
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig_corr, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# PAGE 3 — Model Performance & SHAP
# ══════════════════════════════════════════════════════════════
elif page == "🤖 Model Performance & SHAP":
    st.markdown('<p class="main-header">Model Performance & SHAP</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Evaluate model accuracy and understand feature contributions</p>',
                unsafe_allow_html=True)

    st.info("**Model trained on 400,000 rows. Evaluated on 100,000 rows (test set).**")

    # ── Row 1: Metrics + Confusion Proxy ──
    m1, m2, m3 = st.columns(3)
    m1.metric("RF Accuracy", "0.91")
    m2.metric("XGBoost Accuracy", "0.93")
    m3.metric("Best Model", "XGBoost", delta="↑ +2pp vs RF")

    st.markdown("")
    st.markdown("##### Predicted Churn Type Distribution (Test Set)")
    st.caption("Confusion matrix skipped — actual labels not available in predictions CSV.")

    pred_dist = pred_df["predicted_churn_type"].value_counts().reset_index()
    pred_dist.columns = ["Predicted Class", "Count"]
    fig_pred = px.bar(
        pred_dist, x="Predicted Class", y="Count",
        title="Class Distribution of predicted_churn_type",
        color="Predicted Class",
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig_pred.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_pred, use_container_width=True)

    # ── Row 2: SHAP Section ──
    st.markdown("---")
    st.subheader("🔬 SHAP Analysis")
    st.info("Run `churn_pipeline.py` first and save `shap_values.pkl` and `shap_explainer.pkl` to load SHAP plots here.")

    shap_file = st.file_uploader("Upload shap_values.npy", type="npy", key="shap_npy")
    shap_loaded = False

    if shap_file is not None:
        try:
            shap_values = np.load(shap_file, allow_pickle=True)
            # Assume shape (n_samples, n_features) — compute mean |SHAP|
            mean_abs = np.mean(np.abs(shap_values), axis=0)
            # Try to get feature names from main dataset numeric cols
            numeric_cols = main_df.select_dtypes(include="number").columns.tolist()
            if len(mean_abs) <= len(numeric_cols):
                feature_names = numeric_cols[:len(mean_abs)]
            else:
                feature_names = [f"Feature {i}" for i in range(len(mean_abs))]
            shap_imp = pd.DataFrame({"Feature": feature_names, "Mean |SHAP|": mean_abs})
            shap_imp = shap_imp.nlargest(15, "Mean |SHAP|")

            fig_shap = px.bar(
                shap_imp, y="Feature", x="Mean |SHAP|", orientation="h",
                title="Feature Importance (SHAP Mean |value|)",
                color="Mean |SHAP|",
                color_continuous_scale="Viridis",
            )
            fig_shap.update_layout(**PLOTLY_LAYOUT, yaxis=dict(autorange="reversed"))
            fig_shap.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_shap, use_container_width=True)
            shap_loaded = True
        except Exception as e:
            st.error(f"Error loading SHAP values: {e}")

    shap_img = st.file_uploader("Upload SHAP summary plot image", type=["png", "jpg"], key="shap_img")
    if shap_img is not None:
        st.image(shap_img, caption="SHAP Summary Plot", use_container_width=True)

    # ── Row 3: Fallback Feature Variance ──
    if not shap_loaded:
        st.markdown("---")
        st.subheader("📊 Proxy Feature Variance (SHAP not loaded)")
        numeric_df = main_df.select_dtypes(include="number")
        variances = numeric_df.var().sort_values(ascending=False).head(15).reset_index()
        variances.columns = ["Feature", "Variance"]

        fig_var = px.bar(
            variances, y="Feature", x="Variance", orientation="h",
            title="Proxy Feature Variance (SHAP not loaded)",
            color="Variance",
            color_continuous_scale="Plasma",
        )
        fig_var.update_layout(**PLOTLY_LAYOUT, yaxis=dict(autorange="reversed"))
        fig_var.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_var, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# PAGE 4 — AI Strategic Recommendations
# ══════════════════════════════════════════════════════════════
elif page == "💡 AI Strategic Recommendations":
    st.markdown('<p class="main-header">AI Strategic Recommendations</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Claude-powered, data-driven strategy for your telecom business</p>',
                unsafe_allow_html=True)

    st.info("This page uses the **Anthropic Claude API**. Add your API key to continue.")

    if "anthropic_key" not in st.session_state:
        st.session_state.anthropic_key = ""
    if "ai_response" not in st.session_state:
        st.session_state.ai_response = None

    api_key = st.text_input("Anthropic API Key", type="password",
                            value=st.session_state.anthropic_key)
    st.session_state.anthropic_key = api_key

    # ── Segment selectors ──
    s1, s2, s3 = st.columns(3)
    regions = ["All"] + sorted(main_df["region"].unique().tolist())
    plans = ["All"] + sorted(main_df["plan_tier"].unique().tolist())
    bundles = ["All"] + sorted(main_df["bundle_name"].unique().tolist())

    with s1:
        sel_reg = st.selectbox("Region", regions)
    with s2:
        sel_plan = st.selectbox("Plan Tier", plans)
    with s3:
        sel_bun = st.selectbox("Bundle Name", bundles)

    b1, b2 = st.columns([1, 1])
    generate = b1.button("🚀 Generate Recommendation", type="primary", use_container_width=True)

    if b2.button("🔄 Regenerate", use_container_width=True):
        st.session_state.ai_response = None
        st.rerun()

    if generate:
        if not api_key:
            st.error("Please provide your Anthropic API key.")
        else:
            with st.spinner("Analysing segment data & calling Claude…"):
                # ── Filter segment ──
                seg = main_df.copy()
                if sel_reg != "All":
                    seg = seg[seg["region"] == sel_reg]
                if sel_plan != "All":
                    seg = seg[seg["plan_tier"] == sel_plan]
                if sel_bun != "All":
                    seg = seg[seg["bundle_name"] == sel_bun]

                seg_pred = pred_df[pred_df["customer_id"].isin(seg["customer_id"])]

                # ── Compute stats ──
                cust_count = len(seg)
                avg_churn_rate = seg["churn"].mean() * 100 if len(seg) > 0 else 0
                avg_arpu_seg = seg["monthly_arpu"].mean() if len(seg) > 0 else 0
                avg_clv_seg = seg_pred["clv"].mean() if len(seg_pred) > 0 else 0
                avg_comp_churn = seg_pred["P(Company_Churn)"].mean() if len(seg_pred) > 0 else 0
                top_contracts = seg["contract_type"].value_counts().head(3).index.tolist() if len(seg) > 0 else []
                avg_tickets = seg["support_tickets_6mo"].mean() if len(seg) > 0 else 0
                avg_net_score = seg["avg_network_score"].mean() if len(seg) > 0 else 0

                stats_text = (
                    f"Customer count: {cust_count:,}\n"
                    f"Avg churn rate: {avg_churn_rate:.2f}%\n"
                    f"Avg ARPU: ₹{avg_arpu_seg:,.0f}\n"
                    f"Avg CLV: ₹{avg_clv_seg:,.0f}\n"
                    f"Avg P(Company_Churn): {avg_comp_churn:.4f}\n"
                    f"Top 3 contract types: {', '.join(top_contracts)}\n"
                    f"Avg support tickets (6mo): {avg_tickets:.2f}\n"
                    f"Avg network score: {avg_net_score:.2f}\n"
                    f"Segment filters — Region: {sel_reg}, Plan Tier: {sel_plan}, Bundle: {sel_bun}"
                )

                prompt = (
                    "You are a telecom strategy consultant advising an Indian telecom company. "
                    "Based on the following customer segment data, provide 4-5 specific, actionable "
                    "business recommendations to reduce churn and increase revenue. Reference real "
                    "Indian telecom strategies where relevant (Jio bundling, Airtel Thanks loyalty "
                    "program, Vi RedX priority plans). Format your response with clear numbered "
                    "recommendations, each with a bold title and 2-3 sentences of detail.\n\n"
                    f"Segment data:\n{stats_text}"
                )

                # ── Call Anthropic ──
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    st.session_state.ai_response = response.content[0].text
                except ImportError:
                    st.error("Please install the `anthropic` package: `pip install anthropic`")
                except Exception as e:
                    st.error(f"API Error: {e}")

    if st.session_state.ai_response:
        st.markdown("---")
        st.markdown("### 📋 Recommendation")
        st.markdown(st.session_state.ai_response)


# ══════════════════════════════════════════════════════════════
# PAGE 5 — Customer Segmentation
# ══════════════════════════════════════════════════════════════
elif page == "🎯 Customer Segmentation":
    st.markdown('<p class="main-header">Customer Segmentation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Risk vs Value quadrant analysis of your customer base</p>',
                unsafe_allow_html=True)

    with st.spinner("Computing segmentation quadrants…"):
        # ── Median splits ──
        med_churn = pred_df["P(Company_Churn)"].median()
        med_arpu = pred_df["monthly_arpu"].median()

        def get_quadrant(row):
            high_risk = row["P(Company_Churn)"] >= med_churn
            high_val = row["monthly_arpu"] >= med_arpu
            if high_risk and high_val:
                return "High Risk / High Value"
            elif high_risk and not high_val:
                return "High Risk / Low Value"
            elif not high_risk and high_val:
                return "Low Risk / High Value"
            else:
                return "Low Risk / Low Value"

        pred_seg = pred_df.copy()
        pred_seg["segment_quadrant"] = pred_seg.apply(get_quadrant, axis=1)

        # ── Join tenure_months from main dataset ──
        tenure_map = main_df[["customer_id", "tenure_months"]].drop_duplicates("customer_id")
        pred_seg = pred_seg.merge(tenure_map, on="customer_id", how="left")

        # ── Sample for plotting ──
        sample_size = min(20000, len(pred_seg))
        plot_data = pred_seg.sample(sample_size, random_state=42)

    color_map = {
        "High Risk / High Value": "#ef4444",
        "High Risk / Low Value": "#f97316",
        "Low Risk / High Value": "#22c55e",
        "Low Risk / Low Value": "#d1d5db",
    }

    fig_seg = px.scatter(
        plot_data, x="P(Company_Churn)", y="monthly_arpu",
        color="segment_quadrant",
        color_discrete_map=color_map,
        hover_data=["customer_id", "predicted_churn_type", "monthly_arpu", "clv", "tenure_months"],
        title="Customer Risk vs Value Segmentation",
        labels={"P(Company_Churn)": "P(Company Churn)", "monthly_arpu": "Monthly ARPU (₹)"},
        opacity=0.5,
    )
    fig_seg.add_vline(x=med_churn, line_dash="dash", line_color="white", opacity=0.5,
                      annotation_text=f"Median Churn Prob: {med_churn:.3f}")
    fig_seg.add_hline(y=med_arpu, line_dash="dash", line_color="white", opacity=0.5,
                      annotation_text=f"Median ARPU: ₹{med_arpu:.0f}")
    fig_seg.update_layout(**PLOTLY_LAYOUT, height=600)
    fig_seg.update_traces(marker=dict(size=4))
    st.plotly_chart(fig_seg, use_container_width=True)

    # ── Quadrant summary table ──
    st.subheader("Quadrant Summary")
    quad_summary = pred_seg.groupby("segment_quadrant").agg(
        Count=("customer_id", "count"),
        Pct_of_Total=("customer_id", lambda x: len(x) / len(pred_seg) * 100),
        Avg_ARPU=("monthly_arpu", "mean"),
        Total_Revenue_at_Risk=("revenue_at_risk", "sum"),
        Avg_CLV=("clv", "mean"),
    ).reset_index()
    quad_summary.columns = ["Quadrant", "Count", "% of Total", "Avg ARPU (₹)",
                            "Total Revenue at Risk (₹)", "Avg CLV (₹)"]
    quad_summary["% of Total"] = quad_summary["% of Total"].round(2)
    quad_summary["Avg ARPU (₹)"] = quad_summary["Avg ARPU (₹)"].round(0)
    quad_summary["Total Revenue at Risk (₹)"] = quad_summary["Total Revenue at Risk (₹)"].round(0)
    quad_summary["Avg CLV (₹)"] = quad_summary["Avg CLV (₹)"].round(0)
    st.dataframe(quad_summary, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# PAGE 6 — Segment Bleeding Analysis
# ══════════════════════════════════════════════════════════════
elif page == "🩸 Segment Bleeding Analysis":
    st.markdown('<p class="main-header">Segment Bleeding Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Where are we losing revenue?</p>',
                unsafe_allow_html=True)

    with st.spinner("Joining datasets for bleeding analysis…"):
        merged = pred_df.merge(
            main_df[["customer_id", "region", "plan_tier", "bundle_name", "contract_type", "monthly_arpu"]],
            on="customer_id", how="left", suffixes=("_pred", "_main"),
        ).dropna(subset=["region"])

    tab_names = ["By Region", "By Plan Tier", "By Bundle", "By Contract Type"]
    col_map = {"By Region": "region", "By Plan Tier": "plan_tier",
               "By Bundle": "bundle_name", "By Contract Type": "contract_type"}

    tabs = st.tabs(tab_names)

    for tab, tab_name in zip(tabs, tab_names):
        col = col_map[tab_name]
        with tab:
            agg = merged.groupby(col).agg(
                Total_Revenue_at_Risk=("revenue_at_risk", "sum"),
                Customer_Count=("customer_id", "count"),
                Avg_P_Company_Churn=("P(Company_Churn)", "mean"),
                Avg_ARPU=("monthly_arpu_pred", "mean"),
            ).reset_index().sort_values("Total_Revenue_at_Risk", ascending=False)

            fig_bleed = px.bar(
                agg, y=col, x="Total_Revenue_at_Risk", orientation="h",
                title=f"Revenue at Risk — {tab_name}",
                color="Total_Revenue_at_Risk",
                color_continuous_scale="Reds",
                labels={"Total_Revenue_at_Risk": "Total Revenue at Risk (₹)", col: tab_name.replace("By ", "")},
            )
            fig_bleed.update_layout(**PLOTLY_LAYOUT, yaxis=dict(autorange="reversed"),
                                    coloraxis_showscale=False, height=max(400, len(agg) * 28))
            st.plotly_chart(fig_bleed, use_container_width=True)

            display_agg = agg.rename(columns={
                col: tab_name.replace("By ", ""),
                "Total_Revenue_at_Risk": "Total Revenue at Risk (₹)",
                "Customer_Count": "Customer Count",
                "Avg_P_Company_Churn": "Avg P(Company Churn)",
                "Avg_ARPU": "Avg ARPU (₹)",
            })
            display_agg["Avg P(Company Churn)"] = display_agg["Avg P(Company Churn)"].round(4)
            display_agg["Avg ARPU (₹)"] = display_agg["Avg ARPU (₹)"].round(0)
            display_agg["Total Revenue at Risk (₹)"] = display_agg["Total Revenue at Risk (₹)"].round(0)
            st.dataframe(display_agg, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# PAGE 7 — Retention Planner
# ══════════════════════════════════════════════════════════════
elif page == "🛡️ Retention Planner":
    st.markdown('<p class="main-header">Retention ROI Planner</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Size the opportunity & identify retention-worthy customers</p>',
                unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        retention_cost = st.slider(
            "Fixed retention offer cost per customer (₹)",
            min_value=100, max_value=5000, value=500, step=100
        )
    with sc2:
        churn_threshold = st.slider(
            "Minimum Company Churn Probability threshold",
            min_value=0.1, max_value=0.9, value=0.4, step=0.05
        )

    # ── Logic ──
    eligible = pred_df[
        (pred_df["P(Company_Churn)"] >= churn_threshold) &
        (pred_df["P(Company_Churn)"] * pred_df["clv"] > retention_cost)
    ].copy()

    # Join tenure_months from main dataset
    tenure_map = main_df[["customer_id", "tenure_months"]].drop_duplicates("customer_id")
    eligible = eligible.merge(tenure_map, on="customer_id", how="left")

    # ── KPI Row ──
    ek1, ek2, ek3, ek4 = st.columns(4)
    eligible_count = len(eligible)
    revenue_saved = eligible["revenue_at_risk"].sum()
    retention_spend = eligible_count * retention_cost
    net_roi = ((revenue_saved - retention_spend) / retention_spend * 100) if retention_spend > 0 else 0

    ek1.metric("Eligible Customers", f"{eligible_count:,}")
    ek2.metric("Revenue Saved (if retained)", format_inr(revenue_saved))
    ek3.metric("Total Retention Spend", format_inr(retention_spend))
    ek4.metric("Net ROI", f"{net_roi:,.1f}%",
               delta="Positive" if net_roi > 0 else "Negative",
               delta_color="normal" if net_roi > 0 else "inverse")

    st.markdown("")

    if eligible_count > 0:
        # ── Scatter plot ──
        plot_elig = eligible.sample(min(5000, len(eligible)), random_state=42) if len(eligible) > 5000 else eligible
        fig_ret = px.scatter(
            plot_elig, x="clv", y="P(Company_Churn)",
            size="monthly_arpu", color="revenue_at_risk",
            title="Retention-Worthy Customers",
            labels={"clv": "CLV (₹)", "P(Company_Churn)": "P(Company Churn)",
                    "monthly_arpu": "Monthly ARPU (₹)", "revenue_at_risk": "Revenue at Risk (₹)"},
            color_continuous_scale="YlOrRd",
            hover_data=["customer_id"],
        )
        fig_ret.update_layout(**PLOTLY_LAYOUT, height=550)
        st.plotly_chart(fig_ret, use_container_width=True)

        # ── Table ──
        display_elig = eligible[["customer_id", "monthly_arpu", "tenure_months",
                                 "P(Company_Churn)", "clv", "revenue_at_risk"]].sort_values(
            "revenue_at_risk", ascending=False
        )
        st.dataframe(display_elig, use_container_width=True, hide_index=True, height=400)

        # ── Download ──
        csv_data = display_elig.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Retention Target List",
            data=csv_data,
            file_name="retention_target_list.csv",
            mime="text/csv",
        )
    else:
        st.warning("No customers meet the eligibility criteria with current slider settings. Try lowering the threshold or cost.")


# ══════════════════════════════════════════════════════════════
# PAGE 8 — Bundle Opportunity Analysis
# ══════════════════════════════════════════════════════════════
elif page == "📦 Bundle Opportunity Analysis":
    st.markdown('<p class="main-header">Bundle Upsell Opportunity</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Identify customers ripe for bundle upgrades & size the revenue opportunity</p>',
                unsafe_allow_html=True)

    BUNDLE_UPGRADE_MAP = {
        "No_Bundle":          ("Basic_OTT",       299),
        "Basic_OTT":          ("Entertainment",   399),
        "Entertainment":      ("Premium_OTT",     599),
        "Gaming_Pack":        ("Premium_OTT",     599),
        "Student_Pack":       ("Basic_OTT",       299),
        "Premium_OTT":        ("Family_Bundle",   799),
        "Family_Bundle":      ("Fiber_OTT_Combo", 999),
        "Business_Bundle":    ("Fiber_OTT_Combo", 999),
        "Fiber_OTT_Combo":    (None,              None),
        "International_Roam": (None,              None),
    }

    bundle_threshold = st.slider(
        "Minimum Bundle Switch Probability",
        min_value=0.1, max_value=0.9, value=0.3, step=0.05
    )

    with st.spinner("Computing upsell opportunities…"):
        # ── Filter & Join ──
        bundle_elig = pred_df[pred_df["P(Bundle_Switch)"] >= bundle_threshold].copy()
        bundle_elig = bundle_elig.merge(
            main_df[["customer_id", "bundle_name", "monthly_bundle_cost", "monthly_arpu"]].drop_duplicates("customer_id"),
            on="customer_id", how="left", suffixes=("_pred", "_main"),
        ).dropna(subset=["bundle_name"])

        # ── Map upgrades ──
        bundle_elig["suggested_bundle"] = bundle_elig["bundle_name"].map(
            lambda x: BUNDLE_UPGRADE_MAP.get(x, (None, None))[0]
        )
        bundle_elig["suggested_bundle_cost"] = bundle_elig["bundle_name"].map(
            lambda x: BUNDLE_UPGRADE_MAP.get(x, (None, None))[1]
        )

        # Drop already-top-tier
        bundle_elig = bundle_elig.dropna(subset=["suggested_bundle"])
        bundle_elig["suggested_bundle_cost"] = bundle_elig["suggested_bundle_cost"].astype(float)
        bundle_elig["arpu_delta"] = bundle_elig["suggested_bundle_cost"] - bundle_elig["monthly_bundle_cost"]
        total_upsell = bundle_elig["arpu_delta"].sum()

    # ── KPI Row ──
    bk1, bk2, bk3 = st.columns(3)
    bk1.metric("Upsell-Eligible Customers", f"{len(bundle_elig):,}")
    bk2.metric("Total Monthly Upsell Opportunity", format_inr(total_upsell))
    bk3.metric("Avg ARPU Delta / Customer", f"₹{bundle_elig['arpu_delta'].mean():,.0f}" if len(bundle_elig) > 0 else "₹0")

    st.markdown("")

    if len(bundle_elig) > 0:
        bc1, bc2 = st.columns(2)

        with bc1:
            by_current = bundle_elig.groupby("bundle_name").size().reset_index(name="Count")
            by_current = by_current.sort_values("Count", ascending=False)
            fig_cur = px.bar(
                by_current, x="bundle_name", y="Count",
                title="Upsell Candidates by Current Bundle",
                labels={"bundle_name": "Current Bundle", "Count": "Candidate Count"},
                color="Count", color_continuous_scale="Purples",
            )
            fig_cur.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
            st.plotly_chart(fig_cur, use_container_width=True)

        with bc2:
            by_target = bundle_elig.groupby("suggested_bundle")["arpu_delta"].sum().reset_index()
            by_target = by_target.sort_values("arpu_delta", ascending=False)
            fig_target = px.bar(
                by_target, x="suggested_bundle", y="arpu_delta",
                title="Revenue Opportunity by Target Bundle",
                labels={"suggested_bundle": "Target Bundle", "arpu_delta": "Total ARPU Delta (₹)"},
                color="arpu_delta", color_continuous_scale="Greens",
            )
            fig_target.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
            st.plotly_chart(fig_target, use_container_width=True)

        # ── Sample Table ──
        # Use monthly_arpu from predictions (the _pred column)
        arpu_col = "monthly_arpu_pred" if "monthly_arpu_pred" in bundle_elig.columns else "monthly_arpu"
        display_bundle = bundle_elig[[
            "customer_id", "bundle_name", "suggested_bundle",
            arpu_col, "arpu_delta", "P(Bundle_Switch)"
        ]].sort_values("arpu_delta", ascending=False).head(500)
        display_bundle = display_bundle.rename(columns={arpu_col: "Monthly ARPU (₹)"})
        st.dataframe(display_bundle, use_container_width=True, hide_index=True, height=400)
    else:
        st.warning("No upsell-eligible customers at this threshold. Try lowering the probability slider.")
