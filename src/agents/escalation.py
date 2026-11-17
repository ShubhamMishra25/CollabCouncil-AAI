"""Agent 9: Human Escalation Agent."""

from typing import Dict, Any, Optional
from src.blackboard import Blackboard


class HumanEscalationAgent:
    """Packages irreconcilable trade-offs into an executive dossier and handles human decision-making."""

    def __init__(self, name: str = "Human Escalation Agent", icon: str = "🚨"):
        self.name = name
        self.icon = icon

    @staticmethod
    def prepare_dossier(bb: Blackboard) -> Dict[str, Any]:
        """Compile a structured trade-off package for executive human review."""
        reg = bb.get_finding_by_topic("regulatory_clearance")
        fin = bb.get_finding_by_topic("financial_margin")
        comp = bb.get_finding_by_topic("competitive_landscape")

        reg_data = reg.numbers if reg else {}
        fin_data = fin.numbers if fin else {}
        comp_data = comp.numbers if comp else {}

        options = [
            {
                "id": 1,
                "title": "Abort Launch in Territory",
                "desc": "Cancel market entry to avoid financial loss and competitor pre-emption. Reallocate capital.",
                "directive": "Executive Directive: Cancel market entry. Reallocate capital to higher-margin territories.",
            },
            {
                "id": 2,
                "title": "Subsidize as Strategic Loss-Leader",
                "desc": "Proceed with launch to capture footprint despite negative unit economics.",
                "directive": "Executive Directive: Proceed as strategic loss-leader. Accept subsidized margin deficit.",
            },
            {
                "id": 3,
                "title": "Authorize Emergency Expedited Budget",
                "desc": "Fund expedited compliance retainer ($25K) to attempt compressing regulatory timeline to 8 weeks.",
                "directive": "Executive Directive: Fund emergency compliance retainer to meet 8-week launch window.",
            },
        ]

        return {
            "conflict_id": bb.conflicts[-1].conflict_id if bb.conflicts else "CONF_ESCALATED",
            "issue": bb.conflicts[-1].issue if bb.conflicts else "Irreconcilable Constraint Trade-Off",
            "regulatory": {
                "delay_weeks": reg_data.get("expected_delay_weeks", 0),
                "fee_usd": reg_data.get("fee_usd", 0),
                "certification": reg_data.get("certification_name", "N/A"),
                "reason": reg_data.get("reason", "Statutory process"),
            },
            "financial": {
                "net_margin_pct": fin_data.get("net_margin_pct", 0),
                "net_margin_per_unit": fin_data.get("net_margin_per_unit", 0),
                "landed_cost": fin_data.get("landed_unit_cost", 0),
            },
            "competitive": {
                "primary_rival": comp_data.get("primary_rival", "N/A"),
                "weeks_to_fill_gap": comp_data.get("weeks_to_fill_gap", 99),
                "market_share_pct": comp_data.get("market_share_pct", 0),
            },
            "options": options,
        }

    @staticmethod
    def escalate(
        bb: Blackboard,
        auto_human: bool = True,
        selected_option: int = 1,
        custom_directive: Optional[str] = None,
    ) -> str:
        """Execute escalation, recording the executive decision on the Blackboard."""
        dossier = HumanEscalationAgent.prepare_dossier(bb)

        if custom_directive:
            chosen_text = custom_directive
        else:
            opt = next((o for o in dossier["options"] if o["id"] == selected_option), dossier["options"][0])
            chosen_text = opt["directive"]

        bb.decision_log.append(chosen_text)

        if bb.conflicts:
            bb.conflicts[-1].status = "ESCALATED"
            bb.conflicts[-1].resolution_details = chosen_text

        bb.log_event(
            phase="Human Escalation",
            agent="Human Escalation Agent",
            icon="🚨",
            action="Executive Decision Applied",
            detail=chosen_text,
            level="ERROR",
        )

        return chosen_text
