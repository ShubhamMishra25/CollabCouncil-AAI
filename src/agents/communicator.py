"""Agent 6: Inter-Agent Communication & Sharing Agent."""

from typing import List
from src.blackboard import Blackboard
from src.models import Finding
from src.agents.base import BaseSpecialist


class InterAgentCommunicator:
    """Pub/Sub message broker and event dispatcher for the multi-agent council."""

    @staticmethod
    def register_roster(bb: Blackboard, specialists: List[BaseSpecialist]):
        """Register all specialists and their pub/sub topic subscriptions with the Blackboard."""
        for sp in specialists:
            for topic in sp.subscribes_to:
                bb.register_subscription(topic, sp.name)

    @staticmethod
    def broadcast(finding: Finding, bb: Blackboard) -> List[str]:
        """Post finding to Blackboard, log the event, and return the list of notified subscribers."""
        notified = bb.post_finding(finding)
        bb.log_event(
            phase="Execution & Sharing",
            agent=finding.agent,
            icon="📢",
            action="Published Finding",
            detail=f"Published {finding.id} ({finding.topic}) -> Notified: {', '.join(notified) if notified else 'None (Blackboard recorded)'}",
            level="INFO",
        )
        return notified
