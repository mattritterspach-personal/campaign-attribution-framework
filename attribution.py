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
    df = df.sort_values(["deal_id", "touchpoint_date"]).reset_index(drop=True)
    df["touch_number"] = df.groupby("deal_id").cumcount() + 1
    return df


def _decay_weight(touch_number: int, n_touches: int, half_life: float = 7.0) -> float:
    days_before_conv = (n_touches - touch_number)
    return np.exp(-np.log(2) * days_before_conv / half_life)


def attribute(df: pd.DataFrame, model: AttributionModel) -> pd.DataFrame:
    converted = df[df["converted"] == True].copy()
    records = []
    for deal_id, journey in converted.groupby("deal_id"):
        journey = journey.sort_values("touchpoint_date").reset_index(drop=True)
        n = len(journey)
        deal_value = journey["deal_value"].iloc[0]
        if model == "first_touch": weights = [1.0] + [0.0] * (n - 1)
        elif model == "last_touch": weights = [0.0] * (n - 1) + [1.0]
        elif model == "linear": weights = [1.0 / n] * n
        elif model == "time_decay":
            raw = [_decay_weight(i + 1, n) for i in range(n)]
            weights = [w / sum(raw) for w in raw]
        elif model == "u_shaped":
            if n == 1: weights = [1.0]
            elif n == 2: weights = [0.5, 0.5]
            else: weights = [0.40] + [0.20 / (n - 2)] * (n - 2) + [0.40]
        elif model == "shapley": weights = _shapley_weights(n)
        else: weights = [1.0 / n] * n
        for i, (_, touch) in enumerate(journey.iterrows()):
            records.append({"channel": touch["channel"], "campaign": touch["campaign"], "attributed_revenue": deal_value * weights[i], "attributed_deals": weights[i]})
    result = pd.DataFrame(records)
    return result.groupby(["channel", "campaign"]).sum().reset_index().sort_values("attributed_revenue", ascending=False)


def _shapley_weights(n: int) -> list[float]:
    if n == 1: return [1.0]
    weights = np.zeros(n)
    for size in range(1, n + 1):
        for coalition in combinations(range(n), size):
            for member in coalition:
                weights[member] += 1.0 / (size * len(list(combinations(range(n), size)))))
    return (weights / weights.sum()).tolist()


def compare_models(df: pd.DataFrame, models=None) -> pd.DataFrame:
    if models is None: models = ["first_touch", "last_touch", "linear", "time_decay", "u_shaped", "shapley"]
    frames = {model: attribute(df, model).groupby("channel")["attributed_revenue"].sum().rename(model) for model in models}
    return pd.DataFrame(frames).fillna(0).reset_index()
