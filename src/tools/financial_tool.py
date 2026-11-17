"""Financial modeling tool calculating unit economics, margins, elasticity, and cert cost caps."""

import os
import json
from typing import Dict, Any
from src.config import DATA_DIR


class FinancialTool:
    """Deterministic financial modeling tool."""

    @staticmethod
    def query_base(product: str, country: str) -> Dict[str, Any]:
        filepath = os.path.join(DATA_DIR, "financials.json")
        if not os.path.exists(filepath):
            return {}

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        prod = data.get("products", {}).get(product, {})
        ctry = data.get("markets", {}).get(country, {}).get(product, {})
        return {**prod, **ctry}

    @staticmethod
    def calculate_margin(
        product: str,
        country: str,
        cert_cost: float,
        timeline_delay_weeks: int,
        price_adjustment_usd: float = 0.0,
        fixed_cost_reduction_usd: float = 0.0,
        horizon_months: int = 12,
    ) -> Dict[str, Any]:
        """Compute projected financial margins incorporating certification fees, delays, and concessions."""
        params = FinancialTool.query_base(product, country)
        if not params:
            return {"error": f"Missing financial profile for {product} in {country}"}

        unit_cost = params.get("unit_cost", 0.0)
        base_price = params.get("price", 0.0)
        retail_price = base_price + price_adjustment_usd
        duty = params.get("import_duty_pct", 0.0) / 100.0
        logistics = params.get("logistics_cost_per_unit", 0.0)
        fixed_cost = max(0.0, params.get("fixed_launch_cost", 0.0) - fixed_cost_reduction_usd)
        base_vol = params.get("base_monthly_volume_at_demand_100", 0.0)
        delay_cost_wk = params.get("delay_cost_per_week", 0.0)
        min_net_profit = params.get("min_net_profit_usd", 0.0)

        # Price elasticity penalty: +1% price reduces demand ~0.8%
        price_delta_pct = ((retail_price - base_price) / base_price) if base_price > 0 else 0.0
        volume_multiplier = max(0.5, 1.0 - 0.8 * price_delta_pct)

        landed_unit_cost = unit_cost * (1.0 + duty) + logistics
        gross_margin_per_unit = retail_price - landed_unit_cost
        gross_margin_pct = (gross_margin_per_unit / retail_price) * 100.0 if retail_price > 0 else 0.0

        runway_volume = round(base_vol * horizon_months * volume_multiplier)
        total_fixed_investment = fixed_cost + cert_cost + (delay_cost_wk * timeline_delay_weeks)
        fixed_cost_per_unit = total_fixed_investment / runway_volume if runway_volume > 0 else 0.0

        net_margin_per_unit = gross_margin_per_unit - fixed_cost_per_unit
        net_margin_pct = (net_margin_per_unit / retail_price) * 100.0 if retail_price > 0 else 0.0

        total_net_profit = (gross_margin_per_unit * runway_volume) - total_fixed_investment

        # Capped certification cost that preserves viability
        cert_cost_cap = max(
            0.0,
            (gross_margin_per_unit * runway_volume) - fixed_cost - (delay_cost_wk * timeline_delay_weeks) - min_net_profit,
        )

        return {
            "retail_price": round(retail_price, 2),
            "landed_unit_cost": round(landed_unit_cost, 2),
            "gross_margin_pct": round(gross_margin_pct, 1),
            "gross_margin_per_unit": round(gross_margin_per_unit, 2),
            "net_margin_pct": round(net_margin_pct, 1),
            "net_margin_per_unit": round(net_margin_per_unit, 2),
            "runway_volume": runway_volume,
            "total_fixed_overhead": round(total_fixed_investment, 2),
            "total_net_profit": round(total_net_profit, 2),
            "is_net_positive": net_margin_per_unit > 0,
            "cert_cost_cap": round(cert_cost_cap, 2),
        }
