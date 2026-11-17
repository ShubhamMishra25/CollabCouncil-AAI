"""Competitor intelligence data access tool."""

import os
from typing import Dict, Any
import pandas as pd
from src.config import DATA_DIR


class CompetitorTool:
    """Deterministic tool to query competitor market share, threat level, and lead-time windows."""

    @staticmethod
    def query(product: str, country: str) -> Dict[str, Any]:
        filepath = os.path.join(DATA_DIR, "competitors.csv")
        if not os.path.exists(filepath):
            return {
                "primary_rival": "None identified",
                "threat_level": "Low",
                "weeks_to_fill_gap": 99,
                "market_share_pct": 0,
            }

        df = pd.read_csv(filepath)
        sub = df[(df["product"] == product) & (df["country"] == country)]
        if sub.empty:
            return {
                "primary_rival": "None identified",
                "threat_level": "Low",
                "weeks_to_fill_gap": 99,
                "market_share_pct": 0,
            }

        top = sub.sort_values(by="market_share_pct", ascending=False).iloc[0]
        return {
            "primary_rival": str(top["competitor"]),
            "market_share_pct": float(top["market_share_pct"]),
            "likely_next_move": str(top["likely_next_move"]),
            "weeks_to_fill_gap": int(top["estimated_weeks_to_fill_a_gap"]),
        }
