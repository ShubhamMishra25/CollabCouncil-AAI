"""Agent 3: Regulatory & Compliance Specialist Agent."""

from src.agents.base import BaseSpecialist
from src.blackboard import Blackboard
from src.models import Finding
from src.tools.regulatory_tool import RegulatoryTool
from src.llm import llm


class RegulatorySpecialist(BaseSpecialist):
    """Analyzes legal, import, certification, and timeline impacts in target jurisdictions."""

    def __init__(self):
        super().__init__(
            name="Regulatory & Compliance Specialist",
            domain="Regulatory Clearance",
            icon="⚖️",
            subscribes_to=[],
        )

    def execute(self, bb: Blackboard) -> Finding:
        p = bb.goal.get("product", "Unknown")
        c = bb.goal.get("country", "Unknown")
        raw = RegulatoryTool.query(p, c)

        weeks = raw.get("expected_delay_weeks", 0)
        fee = raw.get("fee_usd", 0)
        has_blocker = raw.get("has_blocker", False)
        blocker_desc = raw.get("reason", "")
        certs = raw.get("certification_name", "Statutory Certification")

        system_instruction = (
            f"You are the {self.name} at Nova Devices. Output a concise 2-sentence regulatory review "
            f"focusing strictly on certifications, statutory timeline delays, and fees."
        )
        prompt = (
            f"Product: {p}, Country: {c}, Certifications: {certs}, "
            f"Expected Delay: {weeks} weeks, Fee: ${fee:,}, Blocker: {has_blocker} ({blocker_desc})."
        )

        try:
            reasoning = llm(system_instruction, prompt)
        except Exception:
            reasoning = (
                f"Statutory compliance requires {certs} adding "
                f"+{weeks} weeks delay and ${fee:,} in filing fees."
            )

        return Finding(
            id="F_REG_01",
            agent=self.name,
            topic="regulatory_clearance",
            claim=reasoning,
            numbers={
                "expected_delay_weeks": weeks,
                "fee_usd": fee,
                "has_blocker": has_blocker,
                "blocker": has_blocker,
                "reason": blocker_desc,
                "certification_name": certs,
                "required_certifications": raw.get("required_certifications", []),
            },
            assumptions_version=bb.assumptions_version,
            confidence=0.98,
        )
