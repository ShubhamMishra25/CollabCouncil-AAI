"""Agent 2: Market Research Specialist Agent."""

from src.agents.base import BaseSpecialist
from src.blackboard import Blackboard
from src.models import Finding
from src.tools.market_tool import MarketTool
from src.llm import llm


class MarketResearchSpecialist(BaseSpecialist):
    """Analyzes market size, demand signals, and regional consumer adoption patterns."""

    def __init__(self):
        super().__init__(
            name="Market Research Specialist",
            domain="Market Demand",
            icon="📈",
            subscribes_to=[],
        )

    def execute(self, bb: Blackboard) -> Finding:
        p = bb.goal.get("product", "Unknown")
        c = bb.goal.get("country", "Unknown")
        raw = MarketTool.query(p, c)

        system_instruction = (
            f"You are the {self.name} at Nova Devices. Output a concise 2-sentence market demand evaluation "
            f"incorporating the provided figures accurately."
        )
        prompt = f"Product: {p}, Country: {c}, Metrics: {raw}."

        try:
            reasoning = llm(system_instruction, prompt)
        except Exception:
            reasoning = (
                f"Target market exhibits demand index of {raw.get('demand_index', 'N/A')} with estimated "
                f"TAM of ${raw.get('tam_usd', 'N/A'):,}. Segment growth is projected at {raw.get('growth_rate_pct', 'N/A')}%."
            )

        return Finding(
            id="F_MKT_01",
            agent=self.name,
            topic="market_demand",
            claim=reasoning,
            numbers=raw,
            assumptions_version=bb.assumptions_version,
            confidence=0.92,
        )
