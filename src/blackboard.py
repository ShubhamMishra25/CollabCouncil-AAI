"""Shared Blackboard architecture with Pub/Sub message broker and versioned consistency."""

import time
from typing import Dict, List, Any, Optional, Set
from src.models import Finding, BlackboardMessage, ConflictRecord, ExecutionLogEntry


class Blackboard:
    """Central shared data repository and communication substrate for all specialist agents."""

    def __init__(self, goal: Dict[str, Any]):
        self.goal = goal
        self.assumptions_version = 1
        self.constraints: Dict[str, Any] = {
            "target_lead_time_weeks": None,
            "timeline_shift_weeks": 0,
            "cert_cost_cap": float("inf"),
            "price_adjustment_usd": 0.0,
            "fixed_cost_reduction_usd": 0.0,
            "soft_launch_allowed": True,
        }
        self.findings: Dict[str, Finding] = {}
        self.message_log: List[BlackboardMessage] = []
        self.conflicts: List[ConflictRecord] = []
        self.decision_log: List[str] = []
        self.execution_logs: List[ExecutionLogEntry] = []
        self.stale_finding_ids: Set[str] = set()

        # Pub/Sub registry: topic -> list of subscribed agent names
        self.subscriptions: Dict[str, List[str]] = {}

        # Dependency graph: when an upstream topic updates, which dependent topics become stale?
        self.topic_dependencies: Dict[str, List[str]] = {
            "regulatory_clearance": ["financial_margin", "launch_timeline"],
            "launch_timeline": ["financial_margin"],
            "identity_&_attack_surface": ["cloud_infrastructure_tco", "sprint_velocity_&_team_readiness"],
        }

    def register_subscription(self, topic: str, agent_name: str):
        """Subscribe an agent to updates on a given topic."""
        self.subscriptions.setdefault(topic, [])
        if agent_name not in self.subscriptions[topic]:
            self.subscriptions[topic].append(agent_name)

    def set_constraint(
        self,
        key: str,
        value: Any,
        increment_version: bool = True,
        dependent_topics: Optional[List[str]] = None,
    ):
        """Update a shared constraint and flag dependent findings as stale."""
        self.constraints[key] = value
        if increment_version:
            self.assumptions_version += 1
            topics_to_invalidate = dependent_topics or self.topic_dependencies.get(
                key, ["financial_margin", "launch_timeline"]
            )
            for fid, f in self.findings.items():
                if f.topic in topics_to_invalidate and f.assumptions_version < self.assumptions_version:
                    self.stale_finding_ids.add(fid)

    def post_finding(self, finding: Finding) -> List[str]:
        """Post a specialist finding to the Blackboard, clear stale status, and notify subscribers."""
        self.findings[finding.id] = finding
        if finding.id in self.stale_finding_ids:
            self.stale_finding_ids.remove(finding.id)

        subscribers = [
            ag for ag in self.subscriptions.get(finding.topic, []) if ag != finding.agent
        ]
        for sub_agent in subscribers:
            self.log_message(finding.agent, sub_agent, finding.id, finding.topic)
        return subscribers

    def log_message(self, sender: str, receiver: str, finding_id: str, topic: str):
        """Record an inter-agent pub/sub communication event."""
        self.message_log.append(
            BlackboardMessage(
                sender=sender,
                receiver=receiver,
                finding_id=finding_id,
                topic=topic,
                timestamp=time.time(),
            )
        )

    def log_event(
        self,
        phase: str,
        agent: str,
        icon: str,
        action: str,
        detail: str,
        level: str = "INFO",
    ):
        """Record an execution step for real-time visualization."""
        self.execution_logs.append(
            ExecutionLogEntry(
                timestamp=time.time(),
                phase=phase,
                agent=agent,
                icon=icon,
                action=action,
                detail=detail,
                level=level,
            )
        )

    def get_finding_by_topic(self, topic: str) -> Optional[Finding]:
        """Retrieve the latest finding for a given topic."""
        for f in reversed(list(self.findings.values())):
            if f.topic == topic:
                return f
        return None

    def get_findings_by_agent(self, agent_name: str) -> List[Finding]:
        """Retrieve all findings published by a specific agent."""
        return [f for f in self.findings.values() if f.agent == agent_name]
