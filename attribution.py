"""
Multi-Touch Attribution Engine
Supports: First Touch, Last Touch, Linear, Time Decay,
          U-Shaped, W-Shaped, and Shapley Value attribution.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from itertools import combinations
from datetime import datetime, timedelta
from typing import Literal


AttributionModel = Literal[
    "first_touch", "last_touch", "linear",
    "time_decay", "u_shaped", "w_shaped", "shapley"
]

CHANNEL_COLORS = {
    "Organic Search": "#4F46E5",
    "Paid Search":    "#7C3AED",
    "Content":        "#A855F7",
    "Social":         "#EC4899",
    "Email":          "#F59E0B",
    "Referral":       "#10B981",
    "Outbound":       "#3B82F6",
    "Event":          "#EF4444",
    "Direct":         "#6B7280",
}


# ─── Sample Data ──────────────────────────────────────────────────────────────

def generate_sample_journeys(n_deals: int = 200, seed: int = 42) -> pd.DataFrame:
    """Generate realistic multi-touch customer journey data."""
    rng = np.random.default_rng(seed)
    channels = list(CHANNEL_COLORS.keys())
    touchpoint_types = ["Ad Click", "Content View", "Email Open", "Demo Request",
                        "Trial Start", "Sales Call", "Proposal Sent"]
    records = []
    for deal_id in range(n_deals):
        n_touches = int(rng.integers(2, 12))
        converted = rng.random() < 0.35
        deal_value = int(rng.integers(5000, 150000)) if converted else 0
        conv_date = datetime(2024, 1, 1) + timedelta(days=int(rng.integers(30, 365)))
        customer_id = f"C{deal_id:05d}"
        for t in range(n_touches):
            days_before = int(rng.integers(0, 90)) + (n_touches - t - 1) * 3
            tp_date = conv_date - timedelta(days=days_before) if converted else \
                      datetime(2024, 1, 1) + timedelta(days=int(rng.integers(0, 300)))
            records.append({
                "customer_id":    customer_id,
                "deal_id":        f"D{deal_id:05d}",
                "touchpoint_date": tp_date,
                "channel":         rng.choice(channels),
                "campaign":        f"Campaign_{rng.integers(1, 20):02d}",
                "touchpoint_type": rng.choice(touchpoint_types),
                "touch_number":    t + 1,
                "n_touches":       n_touches,
                "deal_value":      deal_value,
                "converted":       converted,
                "conversion_date": conv_date if converted else pd.NaT,
            })
    df = pd.DataFrame(records)
    df["touchpoint_date"] = pd.to_datetime(df["touchpoint_date"])
    df["conversion_date"] = pd.to_datetime(df["conversion_date"])
    # Sort and recalculate touch positions
    df = df.sort_values(["deal_id", "touchpoint_date"]).reset_index(drop=True)
    df["touch_number"] = df.groupby("deal_id").cumcount() + 1
    return df


# ─── Attribution Engine ───────────────────────────────────────────────────────

def _decay_weight(touch_number: int, n_touches: int, half_life: float = 7.0) -> float:
    """Exponential time decay weight — more recent = higher weight."""
    days_before_conv = (n_touches - touch_number)
    return np.exp(-np.log(2) * days_before_conv / half_life)


def attribute(df: pd.DataFrame, model: AttributionModel) -> pd.DataFrame:
    """
    Apply the specified attribution model to a touchpoints DataFrame.

    Returns a DataFrame with columns: [channel, campaign, attributed_revenue, attributed_deals].
    """
    converted = df[df["converted"] == True].copy()
    if len(converted) == 0:
        return pd.DataFrame(columns=["channel", "campaign", "attributed_revenue", "attributed_deals"])

    records = []

    for deal_id, journey in converted.groupby("deal_id"):
        journey = journey.sort_values("touchpoint_date").reset_index(drop=True)
        n = len(journey)
        deal_value = journey["deal_value"].iloc[0]

        if model == "first_touch":
            weights = [1.0] + [0.0] * (n - 1)

        elif model == "last_touch":
            weights = [0.0] * (n - 1) + [1.0]

        elif model == "linear":
            weights = [1.0 / n] * n

        elif model == "time_decay":
            raw = [_decay_weight(i + 1, n) for i in range(n)]
            total = sum(raw)
            weights = [w / total for w in raw]

        elif model == "u_shaped":
            if n == 1:
                weights = [1.0]
            elif n == 2:
                weights = [0.5, 0.5]
            else:
                middle_weight = 0.20 / max(n - 2, 1)
                weights = [0.40] + [middle_weight] * (n - 2) + [0.40]

        elif model == "w_shaped":
            # 30% first, 30% MQL (middle), 30% last, 10% others
            if n <= 3:
                weights = [1.0 / n] * n
            else:
                mid_idx = n // 2
                base = 0.10 / max(n - 3, 1)
                weights = [base] * n
                weights[0]       = 0.30
                weights[mid_idx] = 0.30
                weights[-1]      = 0.30
                # Normalize others
                others_sum = sum(weights[i] for i in range(n) if i not in [0, mid_idx, n-1])
                for i in range(1, n - 1):
                    if i != mid_idx:
                        weights[i] = 0.10 / max(n - 3, 1)
                total = sum(weights)
                weights = [w / total for w in weights]

        elif model == "shapley":
            weights = _shapley_weights(n)

        else:
            raise ValueError(f"Unknown model: {model}")

        for i, (_, touch) in enumerate(journey.iterrows()):
            records.append({
                "channel":            touch["channel"],
                "campaign":           touch["campaign"],
                "attributed_revenue": deal_value * weights[i],
                "attributed_deals":   weights[i],
            })

    result = pd.DataFrame(records)
    return (
        result.groupby(["channel", "campaign"])
        .sum()
        .reset_index()
        .sort_values("attributed_revenue", ascending=False)
    )


def _shapley_weights(n: int) -> list[float]:
    """
    Approximate Shapley value weights for n touchpoints.
    Based on marginal contribution averaging across all orderings.
    Simplified: each position's weight is proportional to 1/k where k is coalition size.
    """
    if n == 1:
        return [1.0]
    weights = np.zeros(n)
    for size in range(1, n + 1):
        for coalition in combinations(range(n), size):
            for member in coalition:
                weights[member] += 1.0 / (size * len(list(combinations(range(n), size))))
    return (weights / weights.sum()).tolist()


def compare_models(df: pd.DataFrame, models: list[AttributionModel] = None) -> pd.DataFrame:
    """Run all models and return a side-by-side comparison by channel."""
    if models is None:
        models = ["first_touch", "last_touch", "linear", "time_decay", "u_shaped", "w_shaped", "shapley"]
    frames = {}
    for model in models:
        result = attribute(df, model)
        channel_agg = result.groupby("channel")["attributed_revenue"].sum().rename(model)
        frames[model] = channel_agg
    return pd.DataFrame(frames).fillna(0).reset_index()


# ─── Charts ───────────────────────────────────────────────────────────────────

def plot_attribution_bars(comparison_df: pd.DataFrame, model: str) -> go.Figure:
    """Bar chart of attributed revenue by channel for a single model."""
    data = comparison_df[["channel", model]].sort_values(model, ascending=True)
    colors = [CHANNEL_COLORS.get(ch, "#888888") for ch in data["channel"]]
    fig = go.Figure(go.Bar(
        x=data[model], y=data["channel"],
        orientation="h",
        marker_color=colors,
        text=[f"${v:,.0f}" for v in data[model]],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Attributed Revenue — {model.replace('_', ' ').title()}",
        xaxis_title="Attributed Revenue ($)",
        height=400,
    )
    return fig


def plot_model_comparison(comparison_df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart comparing attribution across all models."""
    models = [c for c in comparison_df.columns if c != "channel"]
    fig = go.Figure()
    for model in models:
        fig.add_trace(go.Bar(
            name=model.replace("_", " ").title(),
            x=comparison_df["channel"],
            y=comparison_df[model],
        ))
    fig.update_layout(
        barmode="group",
        title="Attribution Model Comparison by Channel",
        xaxis_title="Channel",
        yaxis_title="Attributed Revenue ($)",
        height=480,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def plot_channel_delta(comparison_df: pd.DataFrame, model_a: str, model_b: str) -> go.Figure:
    """Waterfall showing delta in attributed revenue between two models."""
    delta = comparison_df[["channel"]].copy()
    delta["delta"] = comparison_df[model_b] - comparison_df[model_a]
    delta = delta.sort_values("delta")
    colors = ["#EF4444" if d < 0 else "#10B981" for d in delta["delta"]]
    fig = go.Figure(go.Bar(
        x=delta["channel"], y=delta["delta"],
        marker_color=colors,
        text=[f"${d:+,.0f}" for d in delta["delta"]],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Revenue Delta: {model_b.replace('_',' ').title()} vs {model_a.replace('_',' ').title()}",
        yaxis_title="Revenue Difference ($)",
        height=400,
    )
    return fig


def plot_journey_sankey(df: pd.DataFrame, top_n_channels: int = 6) -> go.Figure:
    """Sankey diagram of common customer journey paths."""
    converted = df[df["converted"] == True].copy()
    converted = converted.sort_values(["deal_id", "touchpoint_date"])

    top_channels = converted["channel"].value_counts().head(top_n_channels).index.tolist()
    converted["channel_clean"] = converted["channel"].apply(
        lambda x: x if x in top_channels else "Other"
    )

    # Build bigrams
    pairs = []
    for _, journey in converted.groupby("deal_id"):
        channels = journey["channel_clean"].tolist()
        for i in range(len(channels) - 1):
            pairs.append((channels[i], channels[i + 1]))

    pair_counts = pd.Series(pairs).value_counts().head(30).reset_index()
    pair_counts.columns = ["pair", "count"]
    pair_counts[["source", "target"]] = pd.DataFrame(pair_counts["pair"].tolist())

    nodes = list(set(pair_counts["source"].tolist() + pair_counts["target"].tolist()))
    node_idx = {n: i for i, n in enumerate(nodes)}

    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, color=["#4F46E5"] * len(nodes)),
        link=dict(
            source=[node_idx[s] for s in pair_counts["source"]],
            target=[node_idx[t] for t in pair_counts["target"]],
            value=pair_counts["count"].tolist(),
        ),
    ))
    fig.update_layout(title="Customer Journey Flow (Top Channel Paths)", height=480)
    return fig
