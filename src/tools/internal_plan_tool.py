"""Internal company plan data access tool."""

import os
import json
from typing import Dict, Any
from src.config import DATA_DIR


class InternalPlanTool:
    """Deterministic tool to query company internal launch targets and marketing commitments."""

    @staticmethod
    def query() -> Dict[str, Any]:
        filepath = os.path.join(DATA_DIR, "internal_plan.json")
        if not os.path.exists(filepath):
            return {
                "target_lead_time_weeks": 8,
                "ad_committed_usd": 50000,
                "soft_launch_allowed": True,
            }

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        plan = data.get("internal_plan", {})
        return {
            "target_lead_time_weeks": plan.get("target_lead_time_weeks", 8),
            "ad_committed_usd": plan.get("ad_committed_usd", 50000),
            "soft_launch_allowed": plan.get("soft_launch_allowed", True),
        }
