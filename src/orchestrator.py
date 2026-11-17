"""Master Orchestrator coordinating the multi-agent collaboration lifecycle."""

import json
from typing import Dict, List, Any, Optional, Callable
from src.blackboard import Blackboard
from src.models import RecommendationClause, Finding
from src.agents.base import BaseSpecialist
from src.agents.decomposer import GoalDecompositionAgent
from src.agents.market import MarketResearchSpecialist
from src.agents.regulatory import RegulatorySpecialist
from src.agents.marketing_plan import MarketingPlanningSpecialist
from src.agents.financial import FinancialSpecialist
from src.agents.competitor import CompetitiveSpecialist
from src.agents.communicator import InterAgentCommunicator
from src.agents.conflict_engine import ConflictNegotiationEngine
from src.agents.consistency import SharedGoalConsistencyAgent
from src.agents.escalation import HumanEscalationAgent
from src.agents.synthesis import TraceableSynthesisEngine
from src.config import DEFAULT_AUTO_HUMAN, DEFAULT_HUMAN_CHOICE


class CollabCouncilOrchestrator:
    """Master orchestrator implementing the 6-phase collaborative multi-agent coordination system."""

    def __init__(
        self,
        goal: Optional[Dict[str, Any]] = None,
        specialists: Optional[List[BaseSpecialist]] = None,
        conflict_handler: Optional[Any] = None,
        escalation_handler: Optional[Any] = None,
        goal_product: Optional[str] = None,
        goal_country: Optional[str] = None,
        auto_human: bool = DEFAULT_AUTO_HUMAN,
        human_choice: int = DEFAULT_HUMAN_CHOICE,
        on_event: Optional[Callable[[str, str, str, str, str], None]] = None,
    ):
        if goal is None and goal_product and goal_country:
            goal = {
                "title": f"Launch {goal_product} in {goal_country} next quarter",
                "product": goal_product,
                "country": goal_country,
            }
        elif goal is None:
            raise ValueError("Provide either `goal` dict or (`goal_product`, `goal_country`).")

        self.bb = Blackboard(goal=goal)
        self.specialists: List[BaseSpecialist] = specialists or [
            MarketResearchSpecialist(),
            RegulatorySpecialist(),
            MarketingPlanningSpecialist(),
            FinancialSpecialist(),
            CompetitiveSpecialist(),
        ]

        self.decomposer = GoalDecompositionAgent()
        self.consistency_agent = SharedGoalConsistencyAgent()
        self.conflict_handler = conflict_handler or ConflictNegotiationEngine()
        self.escalation_handler = escalation_handler or HumanEscalationAgent()
        self.auto_human = auto_human
        self.human_choice = human_choice
        self.on_event = on_event

        # Register pub/sub subscriptions
        InterAgentCommunicator.register_roster(self.bb, self.specialists)

    def _log(self, phase: str, agent: str, icon: str, action: str, detail: str, level: str = "INFO"):
        self.bb.log_event(phase, agent, icon, action, detail, level)
        if self.on_event:
            self.on_event(phase, agent, icon, action, detail)

    def run_pipeline(
        self,
        interactive_human: bool = False,
        interactive_human_choice: Optional[int] = None,
    ) -> List[RecommendationClause]:
        """Execute the complete multi-agent coordination lifecycle."""
        goal_title = self.bb.goal.get("title") or f"{self.bb.goal.get('product')} in {self.bb.goal.get('country')}"

        self._log(
            "Initialization",
            "Orchestrator",
            "🚀",
            "Starting Pipeline",
            f"Initiating CollabCouncil for: {goal_title}",
            level="INFO",
        )

        # -------------------------------------------------------------
        # Phase 1: Goal Decomposition & Workstream Assignment
        # -------------------------------------------------------------
        self._log(
            "Phase 1: Decomposition",
            self.decomposer.name,
            self.decomposer.icon,
            "Decomposing Goal",
            "Decomposing high-level goal into specialized specialist assignments...",
            level="INFO",
        )
        assignments = self.decomposer.decompose(self.bb.goal, self.specialists)
        for sp in self.specialists:
            task = assignments.get(sp.name, f"Assess {sp.domain}")
            self._log(
                "Phase 1: Decomposition",
                self.decomposer.name,
                "📋",
                "Assigned Deliverable",
                f"[{sp.name}] -> {task}",
                level="INFO",
            )

        # -------------------------------------------------------------
        # Phase 2: First-Pass Specialist Execution & Pub/Sub Sharing
        # -------------------------------------------------------------
        self._log(
            "Phase 2: Execution",
            "Orchestrator",
            "🔬",
            "Specialist Execution",
            "Executing specialists and broadcasting findings via Pub/Sub blackboard...",
            level="INFO",
        )
        for sp in self.specialists:
            finding = sp.execute(self.bb)
            notified = InterAgentCommunicator.broadcast(finding, self.bb)
            note = f" (Notified: {', '.join(notified)})" if notified else ""
            self._log(
                "Phase 2: Execution",
                sp.name,
                sp.icon,
                "Published Finding",
                f"{finding.id} ({finding.topic}){note}: {finding.claim}",
                level="INFO",
            )

        # -------------------------------------------------------------
        # Phase 3: Shared Goal Consistency & Stale Invalidation
        # -------------------------------------------------------------
        self._log(
            "Phase 3: Consistency Check",
            self.consistency_agent.name,
            self.consistency_agent.icon,
            "Consistency Scan",
            "Propagating constraints and checking for stale assumptions...",
            level="INFO",
        )
        re_executed = self.consistency_agent.synchronize(self.bb, self.specialists)
        if re_executed:
            self._log(
                "Phase 3: Consistency Check",
                self.consistency_agent.name,
                "🔄",
                "Re-synchronization Complete",
                f"Re-aligned specialists: {', '.join(re_executed)} to blackboard v{self.bb.assumptions_version}",
                level="SUCCESS",
            )
        else:
            self._log(
                "Phase 3: Consistency Check",
                self.consistency_agent.name,
                "✅",
                "Assumptions Aligned",
                "All specialist assumptions are consistent with Blackboard v1.",
                level="INFO",
            )

        # -------------------------------------------------------------
        # Phase 4: Conflict Detection & Structured Negotiation
        # -------------------------------------------------------------
        self._log(
            "Phase 4: Conflict Resolution",
            "Conflict Engine",
            "⚡",
            "Conflict Evaluation",
            "Scanning for cross-agent constraint conflicts and running negotiation...",
            level="INFO",
        )

        if hasattr(self.conflict_handler, "negotiate"):
            status = self.conflict_handler.negotiate(self.bb)
        else:
            status = "NO_CONFLICT"

        # -------------------------------------------------------------
        # Phase 5: Human Escalation (if negotiation unresolved)
        # -------------------------------------------------------------
        if status == "UNRESOLVED":
            choice_to_use = interactive_human_choice or self.human_choice
            self._log(
                "Phase 5: Human Escalation",
                "Human Escalation Agent",
                "🚨",
                "Triggering Human Escalation",
                "Specialist negotiation deadlocked. Invoking human-in-the-loop executive review.",
                level="WARNING",
            )
            self.escalation_handler.escalate(
                self.bb,
                auto_human=not interactive_human,
                selected_option=choice_to_use,
            )

        # -------------------------------------------------------------
        # Phase 6: Traceable Synthesis & Attribution
        # -------------------------------------------------------------
        self._log(
            "Phase 6: Traceable Synthesis",
            "Traceable Synthesis Engine",
            "📝",
            "Synthesizing Recommendation",
            "Generating unified executive recommendation with clause-level attribution...",
            level="INFO",
        )
        clauses = TraceableSynthesisEngine.synthesize(self.bb)

        self._log(
            "Completed",
            "Orchestrator",
            "🎯",
            "Pipeline Complete",
            f"Generated {len(clauses)} attributed recommendation clauses.",
            level="SUCCESS",
        )

        return clauses
