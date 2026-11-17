"""Agent 8: Shared Goal Consistency Agent."""

from typing import List
from src.blackboard import Blackboard
from src.agents.base import BaseSpecialist


class SharedGoalConsistencyAgent:
    """Monitors versioned Blackboard constraints, flags stale assumptions, and re-executes affected specialists."""

    def __init__(self, name: str = "Shared Goal Consistency Agent", icon: str = "🔄"):
        self.name = name
        self.icon = icon

    def synchronize(self, bb: Blackboard, specialists: List[BaseSpecialist]) -> List[str]:
        """Check for upstream constraint shifts, propagate updates, and re-run stale specialists."""
        re_executed = []

        # Check upstream regulatory delay and propagate constraint
        reg_f = bb.get_finding_by_topic("regulatory_clearance")
        if reg_f:
            delay = reg_f.numbers.get("expected_delay_weeks", 0)
            if bb.constraints.get("timeline_shift_weeks") != delay:
                bb.set_constraint("timeline_shift_weeks", delay, increment_version=True)
                bb.log_event(
                    phase="Consistency Check",
                    agent=self.name,
                    icon=self.icon,
                    action="Propagated Constraint",
                    detail=f"timeline_shift_weeks set to +{delay}w (Blackboard at v{bb.assumptions_version})",
                    level="INFO",
                )

        # Detect and re-execute stale findings
        if bb.stale_finding_ids:
            stale_fids = list(bb.stale_finding_ids)
            bb.log_event(
                phase="Consistency Check",
                agent=self.name,
                icon="⚠️",
                action="Stale Assumption Invalidation",
                detail=f"Findings {stale_fids} invalidated due to upstream constraint change. Triggering re-execution.",
                level="WARNING",
            )

            for sp in specialists:
                prior_findings = bb.get_findings_by_agent(sp.name)
                # If this specialist has a stale finding, re-execute it
                if any(f.id in bb.stale_finding_ids for f in prior_findings):
                    refreshed_finding = sp.execute(bb)
                    bb.post_finding(refreshed_finding)
                    re_executed.append(sp.name)
                    bb.log_event(
                        phase="Consistency Check",
                        agent=sp.name,
                        icon=sp.icon,
                        action="Re-executed on Fresh Assumptions",
                        detail=f"Re-published {refreshed_finding.id} under assumptions v{bb.assumptions_version}",
                        level="SUCCESS",
                    )

        return re_executed
