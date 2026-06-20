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


# ─── Sample Data

def generate_sample_journeys(n_deals: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    channels = list(CHANNEL_COLORS.keys())
    records = []
    for deal_id in range(n_deals):
        n_touches = int(rng.integers(2, 12))
        converted = rng.random() < 0.35
        deal_value = int(rng.integers(5000, 150000)) if converted else 0
        for t in range(n_touches):
            records.append({"deal_id": deal_id, "channel": rng.choice(channels), "deal_value": deal_value, "converted": converted, "touch_number": t+1, "n_touches": n_touches})
    return pd.DataFrame(records)
