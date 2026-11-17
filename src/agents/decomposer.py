"""Agent 1: Goal Decomposition & Workstream Assignment Agent."""

import json
from typing import Dict, List, Any
from src.llm import llm
from src.agents.base import BaseSpecialist


class GoalDecompositionAgent:
    """Decomposes a high-level strategic goal into specialized deliverables for the active specialist roster."""

    def __init__(self, name: str = "Goal Decomposition Agent", icon: str = "📋"):
        self.name = name
        self.icon = icon

    def decompose(self, goal: Dict[str, Any], specialists: List[BaseSpecialist]) -> Dict[str, str]:
        """Generate specific workstream assignments for each specialist agent in the roster."""
        goal_desc = goal.get("title") or json.dumps(goal)
        roster_meta = [{"name": s.name, "domain": s.domain} for s in specialists]

        system_instruction = (
            "You are the Goal Decomposition & Workstream Assignment Agent in a collaborative multi-agent council. "
            "Your job is to break the high-level strategic goal into precise 1-sentence analytical deliverables, "
            "assigning each to the appropriate specialist in the roster. "
            "Return strictly valid JSON mapping each specialist's exact 'name' to their assigned deliverable task."
        )

        prompt = (
            f"Goal: {goal_desc}\n"
            f"Active Specialist Roster: {json.dumps(roster_meta, indent=2)}\n\n"
            "Format: { \"<Specialist Name>\": \"<Assigned Deliverable>\" }"
        )

        try:
            raw = llm(system_instruction, prompt, json_mode=True)
            assignments = json.loads(raw)
            if isinstance(assignments, dict):
                # Ensure all specialists have an assignment
                for s in specialists:
                    if s.name not in assignments:
                        assignments[s.name] = f"Evaluate {s.domain} metrics and operational constraints."
                return assignments
        except Exception:
            pass

        # Robust deterministic fallback
        return {
            s.name: f"Evaluate {s.domain} metrics and operational constraints for {goal_desc}"
            for s in specialists
        }
