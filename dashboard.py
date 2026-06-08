"""
Campaign Attribution Dashboard — Streamlit
Compare every attribution model side-by-side.
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
from attribution import (
    generate_sample_journeys, attribute, compare_models,
    plot_attribution_bars, plot_model_comparison, plot_channel_delta, plot_journey_sankey,
)

st.set_page_config(page_title="Campaign Attribution", page_icon="🎯", layout="wide")
st.title("🎯 Campaign Attribution Framework")
st.caption("Compare First Touch, Last Touch, Linear, Time Decay, U-Shaped, W-Shaped, and Shapley Value — side by side.")

# ─── Data ─────────────────────────────────────────────────────────────────────
df = generate_sample_journeys(n_deals=300)
converted = df[df["converted"] == True]
total_deals = df["deal_id"].nunique()
conv_deals = converted["deal_id"].nunique()
total_revenue = converted.drop_duplicates("deal_id")["deal_value"].sum()
avg_touches = df.groupby("deal_id").size().mean()

# ─── KPIs ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Deals", f"{total_deals:,}")
col2.metric("Converted Deals", f"{conv_deals:,}")
col3.metric("Total Revenue", f"${total_revenue:,.0f}")
col4.metric("Avg Touchpoints", f"{avg_touches:.1f}")
st.divider()

# ─── Model Selector ───────────────────────────────────────────────────────────
MODEL_LABELS = {
    "first_touch": "First Touch",
    "last_touch":  "Last Touch",
    "linear":      "Linear",
    "time_decay":  "Time Decay",
    "u_shaped":    "U-Shaped",
    "w_shaped":    "W-Shaped",
    "shapley":     "Shapley Value",
}
selected_model = st.sidebar.selectbox(
    "Primary Attribution Model",
    options=list(MODEL_LABELS.keys()),
    format_func=lambda x: MODEL_LABELS[x],
    index=2,
)
compare_model = st.sidebar.selectbox(
    "Compare Against",
    options=[m for m in MODEL_LABELS.keys() if m != selected_model],
    format_func=lambda x: MODEL_LABELS[x],
    index=0,
)

# ─── Single Model View ────────────────────────────────────────────────────────
st.subheader(f"📊 {MODEL_LABELS[selected_model]} Attribution")
result = attribute(df, selected_model)
channel_summary = result.groupby("channel").agg(
    attributed_revenue=("attributed_revenue", "sum"),
    attributed_deals=("attributed_deals", "sum"),
).reset_index().sort_values("attributed_revenue", ascending=False)
channel_summary["revenue_share"] = channel_summary["attributed_revenue"] / channel_summary["attributed_revenue"].sum()

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(plot_attribution_bars(channel_summary.rename(columns={"attributed_revenue": selected_model}), selected_model), use_container_width=True)
with col_right:
    st.dataframe(
        channel_summary.assign(
            attributed_revenue=channel_summary["attributed_revenue"].apply(lambda x: f"${x:,.0f}"),
            attributed_deals=channel_summary["attributed_deals"].apply(lambda x: f"{x:.1f}"),
            revenue_share=channel_summary["revenue_share"].apply(lambda x: f"{x:.1%}"),
        ).rename(columns={"attributed_revenue": "Revenue", "attributed_deals": "Deals", "revenue_share": "Share"}),
        use_container_width=True, hide_index=True,
    )

st.divider()

# ─── Model Comparison ─────────────────────────────────────────────────────────
st.subheader("⚖️ All Models — Side-by-Side")
comparison = compare_models(df)
st.plotly_chart(plot_model_comparison(comparison), use_container_width=True)

st.subheader(f"📉 Delta: {MODEL_LABELS[selected_model]} vs {MODEL_LABELS[compare_model]}")
st.plotly_chart(plot_channel_delta(comparison, compare_model, selected_model), use_container_width=True)

st.divider()

# ─── Journey Flow ─────────────────────────────────────────────────────────────
st.subheader("🔀 Customer Journey Flow")
st.plotly_chart(plot_journey_sankey(df), use_container_width=True)

# ─── Campaign Breakdown ───────────────────────────────────────────────────────
st.subheader("📋 Campaign-Level Attribution")
campaign_result = result.groupby("campaign").agg(
    attributed_revenue=("attributed_revenue", "sum"),
    attributed_deals=("attributed_deals", "sum"),
).reset_index().sort_values("attributed_revenue", ascending=False).head(20)
st.dataframe(campaign_result, use_container_width=True, hide_index=True)
