"""
Campaign Attribution Dashboard — Streamlit
Compare every attribution model side-by-side.
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
from attribution import (
    generate_sample_journeys, attribute, compare_models,
)

st.set_page_config(page_title="Campaign Attribution", page_icon="🎯", layout="wide")
st.title("🏯 Campaign Attribution Framework")

df = generate_sample_journeys(n_deals=300)
converted = df[df["converted"] == True]
total_deals = df["deal_id"].nunique()
conv_deals = converted["deal_id"].nunique()
total_revenue = converted.drop_duplicates("deal_id")["deal_value"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Deals", f"{total_deals:,}")
col2.metric("Converted Deals", f"{conv_deals:,}")
col3.metric("Total Revenue", f"${total_revenue:,.0f}")
st.divider()

MODEL_LABELS = {"first_touch": "First Touch", "last_touch": "Last Touch", "linear": "Linear", "time_decay": "Time Decay", "u_shaped": "U-Shaped", "shapley": "Shapley Value"}
selected_model = st.sidebar.selectbox("Attribution Model", options=list(MODEL_LABELS.keys()), format_func=lambda x: MODEL_LABELS[x], index=2)

st.subheader(f"Results: {MODEL_LABELS[selected_model]}")
result = attribute(df, selected_model)
channel_summary = result.groupby("channel").agg(attributed_revenue=("attributed_revenue", "sum"), attributed_deals=("attributed_deals", "sum")).reset_index().sort_values("attributed_revenue", ascending=False)
st.dataframe(channel_summary, use_container_width=True, hide_index=True)

st.subheader("Ɩ️ All Models Side-by-Side")
comparison = compare_models(df)
st.dataframe(comparison, use_container_width=True, hide_index=True)
