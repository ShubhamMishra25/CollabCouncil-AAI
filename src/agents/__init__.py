"""CollabCouncil multi-agent roster and coordination agents."""

from src.agents.base import BaseSpecialist
from src.agents.decomposer import GoalDecompositionAgent
from src.agents.market import MarketResearchSpecialist
from src.agents.regulatory import RegulatorySpecialist
from src.agents.financial import FinancialSpecialist
from src.agents.competitor import CompetitiveSpecialist
from src.agents.marketing_plan import MarketingPlanningSpecialist
from src.agents.communicator import InterAgentCommunicator
from src.agents.conflict_engine import ConflictNegotiationEngine
from src.agents.consistency import SharedGoalConsistencyAgent
from src.agents.escalation import HumanEscalationAgent
from src.agents.synthesis import TraceableSynthesisEngine

__all__ = [
    "BaseSpecialist",
    "GoalDecompositionAgent",
    "MarketResearchSpecialist",
    "RegulatorySpecialist",
    "FinancialSpecialist",
    "CompetitiveSpecialist",
    "MarketingPlanningSpecialist",
    "InterAgentCommunicator",
    "ConflictNegotiationEngine",
    "SharedGoalConsistencyAgent",
    "HumanEscalationAgent",
    "TraceableSynthesisEngine",
]
