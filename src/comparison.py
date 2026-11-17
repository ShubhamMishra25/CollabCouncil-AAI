"""Single Generalist LLM vs. CollabCouncil Multi-Agent Team comparison."""

from typing import Dict, Any, List
import pandas as pd
from src.llm import llm


def run_single_generalist(product: str, country: str) -> str:
    """Execute a single generalist LLM pass without access to private internal company databases."""
    prompt = (
        f"Goal: Should Nova Devices launch {product} in {country} next quarter? "
        f"Give a direct business recommendation in 2 sentences."
    )
    system = (
        "You are a general business AI. Provide an executive recommendation without access to private "
        "internal company databases or specific regulatory files."
    )
    return llm(system, prompt)


def get_comparison_matrix() -> pd.DataFrame:
    """Return the structured evaluation dimension comparison matrix."""
    return pd.DataFrame([
        {
            "Evaluation Dimension": "Numeric Grounding",
            "Single Generalist LLM": "None (gives generic strategic advice or hallucinated estimates).",
            "CollabCouncil Multi-Agent System": "Exact numbers dynamically pulled from external datasets (e.g. landed costs, fees, TAM).",
        },
        {
            "Evaluation Dimension": "Conflict Handling",
            "Single Generalist LLM": "Fails to identify precise timing mismatches or calculate exact margin deficits.",
            "CollabCouncil Multi-Agent System": "Identifies cross-functional collisions and runs bounded negotiation rounds with mathematical validation.",
        },
        {
            "Evaluation Dimension": "Cross-Domain Interdependence",
            "Single Generalist LLM": "Isolated analysis; cannot model how a regulatory delay increases delay costs and compresses net margins.",
            "CollabCouncil Multi-Agent System": "Event-driven pub/sub blackboard cascades regulatory updates to recalculate financials and schedule risks.",
        },
        {
            "Evaluation Dimension": "Auditability & Attribution",
            "Single Generalist LLM": "Black-box text generation with no citation of internal operational sources.",
            "CollabCouncil Multi-Agent System": "Every clause in the unified recommendation is traced directly to the contributing specialist and finding ID.",
        },
        {
            "Evaluation Dimension": "Executive Actionability",
            "Single Generalist LLM": "Vague 'proceed with caution' or 'evaluate local market factors'.",
            "CollabCouncil Multi-Agent System": "Definitive action with clear contingency thresholds (e.g. capped certification fees, pre-order bridge).",
        },
    ])
