"""Agent 5: Competitive Intelligence Specialist Agent."""

from src.agents.base import BaseSpecialist
from src.blackboard import Blackboard
from src.models import Finding
from src.tools.competitor_tool import CompetitorTool
from src.llm import llm


class CompetitiveSpecialist(BaseSpecialist):
    """Monitors rival market share, preemptive launches, and timing vulnerabilities."""

    def __init__(self):
        super().__init__(
            name="Competitive Intelligence Specialist",
            domain="Competitive Threats",
            icon="🎯",
            subscribes_to=["launch_timeline", "regulatory_clearance"],
        )

    def execute(self, bb: Blackboard) -> Finding:
        p = bb.goal.get("product", "Unknown")
        c = bb.goal.get("country", "Unknown")
        comp = CompetitorTool.query(p, c)

        reg_f = bb.get_finding_by_topic("regulatory_clearance")
        reg_delay = reg_f.numbers.get("expected_delay_weeks", 0) if reg_f else 0
        comp_gap = comp.get("weeks_to_fill_gap", 99)

        system_instruction = (
            f"You are the {self.name} at Nova Devices. Output a concise 2-sentence competitive landscape assessment. "
            f"Explicitly compare the regulatory timeline delay (+{reg_delay}w) against the rival gap ({comp_gap}w)."
        )
        prompt = f"Product: {p}, Country: {c}, Competitor Profile: {comp}, Projected Delay: {reg_delay} weeks."

        try:
            reasoning = llm(system_instruction, prompt)
        except Exception:
            reasoning = (
                f"Primary rival {comp.get('primary_rival', 'Unknown')} holds {comp.get('market_share_pct', 0)}% market share. "
                f"They require approximately {comp_gap} weeks to fill market voids, compared against our {reg_delay}-week delay."
            )

        depends = [reg_f.id] if reg_f else []

        return Finding(
            id="F_CMP_01",
            agent=self.name,
            topic="competitive_landscape",
            claim=reasoning,
            numbers={**comp, "delay_risk_critical": reg_delay >= comp_gap},
            assumptions_version=bb.assumptions_version,
            confidence=0.88,
            depends_on=depends,
        )
