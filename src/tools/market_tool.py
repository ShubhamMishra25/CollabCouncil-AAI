"""Market research data access tool."""

import os
from typing import Dict, Any
import pandas as pd
from src.config import DATA_DIR


class MarketTool:
    """Deterministic tool to query regional market size and consumer demand metrics."""

    @staticmethod
    def query(product: str, country: str) -> Dict[str, Any]:
        filepath = os.path.join(DATA_DIR, "market.csv")
        if not os.path.exists(filepath):
            return {"error": f"Dataset missing: {filepath}"}

        df = pd.read_csv(filepath)
        row = df[(df["product"] == product) & (df["country"] == country)]
        if row.empty:
            return {"error": f"No market data for {product} in {country}"}
        return row.iloc[0].to_dict()
