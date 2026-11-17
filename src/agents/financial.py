"""Agent 4: Financial Modeling Specialist Agent."""

from src.agents.base import BaseSpecialist
from src.blackboard import Blackboard
from src.models import Finding
from src.tools.financial_tool import FinancialTool
from src.llm import llm


class FinancialSpecialist(BaseSpecialist):
    """Builds unit economics models, evaluating cost structures, margin viability, and fee caps."""

    def __init__(self):
        super().__init__(
            name="Financial Modeling Specialist",
            domain="Unit Economics & Margin",
            icon="💰",
            subscribes_to=["regulatory_clearance", "launch_timeline"],
        )

    def execute(self, bb: Blackboard) -> Finding:
        p = bb.goal.get("product", "Unknown")
        c = bb.goal.get("country", "Unknown")

        # Dynamically pull cross-agent findings from Blackboard
        reg_f = bb.get_finding_by_topic("regulatory_clearance")
        cert_cost = float(reg_f.numbers.get("fee_usd", 0.0)) if reg_f else 0.0

        delay_weeks = int(bb.constraints.get("timeline_shift_weeks", 0))
        price_adj = float(bb.constraints.get("price_adjustment_usd", 0.0))
        fixed_red = float(bb.constraints.get("fixed_cost_reduction_usd", 0.0))

        fin_data = FinancialTool.calculate_margin(
            product=p,
            country=c,
            cert_cost=cert_cost,
            timeline_delay_weeks=delay_weeks,
            price_adjustment_usd=price_adj,
            fixed_cost_reduction_usd=fixed_red,
        )

        bb.constraints["cert_cost_cap"] = fin_data.get("cert_cost_cap", float("inf"))

        system_instruction = (
            f"You are the {self.name} at Nova Devices. Output a concise 2-sentence financial health assessment. "
            f"State exact net margin percentage, landed cost, and the certification cost viability cap."
        )
        prompt = (
            f"Product: {p}, Country: {c}, Financial Output: {fin_data}, "
            f"Incorporated Cert Fee: ${cert_cost:,}, Incorporated Delay: +{delay_weeks}w."
        )

        try:
            reasoning = llm(system_instruction, prompt)
        except Exception:
            reasoning = (
                f"Landed unit cost stands at ${fin_data.get('landed_unit_cost', 0):.2f} with projected "
                f"net margin of {fin_data.get('net_margin_pct', 0)}%. Financial viability is preserved if "
                f"certification cost remains capped at ${fin_data.get('cert_cost_cap', 0):,}."
            )

        depends = [reg_f.id] if reg_f else []

        return Finding(
            id="F_FIN_01",
            agent=self.name,
            topic="financial_margin",
            claim=reasoning,
            numbers=fin_data,
            assumptions_version=bb.assumptions_version,
            confidence=0.95,
            depends_on=depends,
        )
