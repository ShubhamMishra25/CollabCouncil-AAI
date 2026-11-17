"""Base class for all specialist agents in CollabCouncil."""

from typing import List, Optional
from src.blackboard import Blackboard
from src.models import Finding


class BaseSpecialist:
    """Abstract base class representing an autonomous specialist agent."""

    def __init__(
        self,
        name: str,
        domain: str,
        icon: str,
        subscribes_to: Optional[List[str]] = None,
    ):
        self.name = name
        self.domain = domain
        self.icon = icon
        self.subscribes_to = subscribes_to or []

    def execute(self, bb: Blackboard) -> Finding:
        """Execute the agent's domain workflow against the current Blackboard state."""
        raise NotImplementedError("Each specialist must implement execute()")
