"""Data models for CollabCouncil multi-agent collaboration."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class Finding:
    """Represents a discrete insight or metric calculated by a specialist agent."""
    id: str
    agent: str
    topic: str
    claim: str
    numbers: Dict[str, Any]
    assumptions_version: int
    confidence: float
    depends_on: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class BlackboardMessage:
    """Represents an event or message dispatched through the Pub/Sub bus."""
    sender: str
    receiver: str
    finding_id: str
    topic: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConflictRecord:
    """Represents a conflict detected between specialist findings and its resolution state."""
    conflict_id: str
    issue: str
    involved_agents: List[str]
    hard_constraints_violated: List[str]
    rounds_run: int
    status: str  # "RESOLVED", "UNRESOLVED", "ESCALATED", "CONSENSUS"
    resolution_details: str = ""
    negotiation_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RecommendationClause:
    """Represents an auditable clause in the final unified executive recommendation."""
    clause_text: str
    source_agents: List[str]
    source_findings: List[str]
    supporting_numbers: Dict[str, Any]


@dataclass
class ExecutionLogEntry:
    """Represents a timestamped event in the orchestrator pipeline for UI streaming."""
    timestamp: float
    phase: str
    agent: str
    icon: str
    action: str
    detail: str
    level: str = "INFO"  # "INFO", "SUCCESS", "WARNING", "ERROR", "NEGOTIATION"
