"""Marketing & Launch Planning Specialist Agent."""

from src.agents.base import BaseSpecialist
from src.blackboard import Blackboard
from src.models import Finding
from src.tools.internal_plan_tool import InternalPlanTool
from src.llm import llm


class MarketingPlanningSpecialist(BaseSpecialist):
    """Aligns go-to-market plans, campaign spend, and launch schedules with cross-functional constraints."""

    def __init__(self):
        super().__init__(
            name="Marketing & Planning Specialist",
            domain="Go-To-Market & Schedule",
            icon="📅",
            subscribes_to=["regulatory_clearance"],
        )

    def execute(self, bb: Blackboard) -> Finding:
        plan = InternalPlanTool.query()

        # Sync target lead time to blackboard constraints
        if bb.constraints.get("target_lead_time_weeks") is None:
            bb.constraints["target_lead_time_weeks"] = plan.get("target_lead_time_weeks", 8)

        # Check for upstream regulatory delay
        reg_f = bb.get_finding_by_topic("regulatory_clearance")
        reg_delay = reg_f.numbers.get("expected_delay_weeks", 0) if reg_f else 0
        target_wks = bb.constraints["target_lead_time_weeks"]

        system_instruction = (
            f"You are the {self.name} at Nova Devices. Output a concise 2-sentence schedule & campaign assessment. "
            f"State clearly whether the original {target_wks}-week target is threatened by any {reg_delay}-week delay."
        )
        prompt = (
            f"Internal Target: {target_wks} weeks, Ad Committed: ${plan.get('ad_committed_usd', 0):,}, "
            f"Regulatory Delay: +{reg_delay} weeks, Soft Launch Allowed: {plan.get('soft_launch_allowed')}."
        )

        try:
            reasoning = llm(system_instruction, prompt)
        except Exception:
            reasoning = (
                f"Marketing target is {target_wks} weeks with ${plan.get('ad_committed_usd', 0):,} committed ad spend. "
                f"Upstream regulatory requirements impose a +{reg_delay} week timeline shift."
            )

        depends = [reg_f.id] if reg_f else []

        return Finding(
            id="F_PLN_01",
            agent=self.name,
            topic="launch_timeline",
            claim=reasoning,
            numbers={
                **plan,
                "effective_delay_weeks": reg_delay,
                "schedule_conflict_weeks": max(0, reg_delay - target_wks),
            },
            assumptions_version=bb.assumptions_version,
            confidence=0.90,
            depends_on=depends,
        )
