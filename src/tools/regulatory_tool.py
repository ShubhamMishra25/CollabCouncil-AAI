"""Regulatory and compliance data access tool with standardized parsing."""

import os
import json
from typing import Dict, Any
from src.config import DATA_DIR


class RegulatoryTool:
    """Deterministic tool to query compliance requirements, certifications, and delay impacts."""

    @staticmethod
    def query(product: str, country: str) -> Dict[str, Any]:
        filepath = os.path.join(DATA_DIR, "regulations.json")
        if not os.path.exists(filepath):
            return {"error": f"Dataset missing: {filepath}"}

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw = data.get(country, {}).get(product, None)
        if not raw:
            return {"error": f"Regulatory record missing for {product} in {country}"}

        # Normalize fields for clean multi-agent consumption
        weeks_dict = raw.get("typical_weeks", {})
        expected_weeks = (
            weeks_dict.get("expected", 0)
            if isinstance(weeks_dict, dict)
            else raw.get("expected_delay_weeks", 0)
        )
        min_weeks = weeks_dict.get("min", expected_weeks) if isinstance(weeks_dict, dict) else expected_weeks
        max_weeks = weeks_dict.get("max", expected_weeks) if isinstance(weeks_dict, dict) else expected_weeks

        blocker_info = raw.get("blocker", {})
        has_blocker = (
            blocker_info.get("has_blocker", False)
            if isinstance(blocker_info, dict)
            else bool(raw.get("blocker", False))
        )
        blocker_desc = (
            blocker_info.get("description", "")
            if isinstance(blocker_info, dict)
            else str(raw.get("reason", ""))
        )

        certs = raw.get("required_certifications", [])
        cert_names = [c["name"] if isinstance(c, dict) else str(c) for c in certs]
        cert_summary = ", ".join(cert_names) if cert_names else "Statutory Compliance Certification"

        return {
            "required_certifications": certs,
            "certification_name": cert_summary,
            "expected_delay_weeks": expected_weeks,
            "min_delay_weeks": min_weeks,
            "max_delay_weeks": max_weeks,
            "fee_usd": raw.get("fee_usd", 0),
            "fee_usd_max": raw.get("fee_usd_max", raw.get("fee_usd", 0)),
            "blocker": has_blocker,
            "has_blocker": has_blocker,
            "reason": blocker_desc,
            "notes": raw.get("notes", ""),
            "raw": raw,
        }
