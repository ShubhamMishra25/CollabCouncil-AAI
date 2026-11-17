"""Alternative Domain: Monolith vs Microservices Migration Pluggable Roster."""

import os
import json
from typing import Dict, Any, List, Optional
from src.agents.base import BaseSpecialist
from src.blackboard import Blackboard
from src.models import Finding, ConflictRecord
from src.llm import llm
from src.config import DATA_DIR


class TechSpecialist(BaseSpecialist):
    """Specialist agent for software engineering, cloud, and architecture decisions."""

    def __init__(
        self,
        name: str,
        domain: str,
        icon: str,
        dataset_file: str,
        subscribes_to: Optional[List[str]] = None,
    ):
        super().__init__(name, domain, icon, subscribes_to=subscribes_to)
        self.dataset_file = dataset_file

    def get_data(self) -> Dict[str, Any]:
        filepath = os.path.join(DATA_DIR, "alt_domain", self.dataset_file)
        if not os.path.exists(filepath):
            filepath = os.path.join(DATA_DIR, self.dataset_file)
        if not os.path.exists(filepath):
            return {}

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(self, bb: Blackboard) -> Finding:
        data = self.get_data()
        system_instruction = (
            f"You are the {self.name}. Summarize your evaluation in 1 clear sentence incorporating key metrics."
        )
        prompt = f"Domain: {self.domain}, Metrics: {data}."

        try:
            claim = llm(system_instruction, prompt)
        except Exception:
            claim = f"{self.domain} analysis complete based on {len(data)} configuration parameters."

        topic_key = self.domain.lower().replace(" ", "_").replace("/", "_").replace("&", "_")
        return Finding(
            id=f"F_{self.name[:3].upper()}_01",
            agent=self.name,
            topic=topic_key,
            claim=claim,
            numbers=data,
            assumptions_version=bb.assumptions_version,
            confidence=0.90,
        )


class TechConflictHandler:
    """Domain-specific conflict rules plugged directly into the generic CollabCouncilOrchestrator."""

    @staticmethod
    def negotiate(bb: Blackboard) -> str:
        sec_f = bb.get_finding_by_topic("identity___attack_surface") or bb.get_finding_by_topic("identity_&_attack_surface")
        dev_f = bb.get_finding_by_topic("sprint_velocity___team_readiness") or bb.get_finding_by_topic("sprint_velocity_&_team_readiness")
        cost_f = bb.get_finding_by_topic("cloud_infrastructure_tco")

        sec_data = sec_f.numbers if sec_f else {}
        dev_data = dev_f.numbers if dev_f else {}
        cost_data = cost_f.numbers if cost_f else {}

        required_eng_weeks = sec_data.get("hardening_baseline_eng_weeks", 0) + (
            cost_data.get("total_services", 0)
            * (dev_data.get("migration_eng_weeks_per_service", 0) + sec_data.get("per_service_security_eng_weeks", 0))
        )
        projected_monthly_cost = cost_data.get("current_infra_monthly_usd", 0) + (
            cost_data.get("total_services", 0) * cost_data.get("incremental_infra_monthly_per_service_usd", 0)
        )
        spare_weeks = dev_data.get("spare_capacity_eng_weeks_this_quarter", 0)
        budget_cap = cost_data.get("infra_budget_cap_monthly_usd", float("inf"))

        if "mTLS" in sec_data.get("hard_rule", "") and required_eng_weeks > spare_weeks:
            proposal_prompt = (
                f"Required engineering weeks: {required_eng_weeks}, Available capacity: {spare_weeks}, "
                f"Hard rule: {sec_data.get('hard_rule')}."
            )
            try:
                proposal = llm(
                    "You are the Engineering Lead Mediator. Propose a 1-sentence phased migration compromise.",
                    proposal_prompt,
                )
            except Exception:
                proposal = "Phase the rollout: Implement identity and mTLS first, delaying service split by 1 quarter."

            resolution = (
                f"Phased Migration Adopted: Execute security baseline and mTLS rollout this quarter before service extraction "
                f"({proposal})."
            )
            bb.conflicts.append(
                ConflictRecord(
                    conflict_id="CONF_TECH_CAP_01",
                    issue=f"Engineering capacity deficit ({required_eng_weeks}w required > {spare_weeks}w available)",
                    involved_agents=[
                        "Security Specialist",
                        "Delivery Capacity Specialist",
                        "DevOps Cost Specialist",
                    ],
                    hard_constraints_violated=[],
                    rounds_run=1,
                    status="RESOLVED",
                    resolution_details=resolution,
                )
            )
            bb.decision_log.append(resolution)
            bb.log_event(
                phase="Conflict Resolution",
                agent="Tech Mediator",
                icon="🔒",
                action="Compromise Reached",
                detail=resolution,
                level="SUCCESS",
            )
            return "RESOLVED"

        if projected_monthly_cost > budget_cap:
            resolution = (
                f"Halt migration: Projected cloud TCO (${projected_monthly_cost:,}/mo) exceeds budget cap "
                f"(${budget_cap:,}/mo)."
            )
            bb.conflicts.append(
                ConflictRecord(
                    conflict_id="CONF_TECH_COST_01",
                    issue=f"Monthly TCO (${projected_monthly_cost:,}) exceeds cap (${budget_cap:,})",
                    involved_agents=["DevOps Cost Specialist", "Delivery Capacity Specialist"],
                    hard_constraints_violated=[],
                    rounds_run=1,
                    status="RESOLVED",
                    resolution_details=resolution,
                )
            )
            bb.decision_log.append(resolution)
            return "RESOLVED"

        return "NO_CONFLICT"


def get_tech_roster() -> List[BaseSpecialist]:
    """Instantiate the pluggable engineering specialist roster."""
    return [
        TechSpecialist("Security Specialist", "Identity & Attack Surface", "🔒", "security.json"),
        TechSpecialist(
            "DevOps Cost Specialist",
            "Cloud Infrastructure TCO",
            "☁️",
            "devops_cost.json",
            subscribes_to=["identity_&_attack_surface"],
        ),
        TechSpecialist(
            "Delivery Capacity Specialist",
            "Sprint Velocity & Team Readiness",
            "⚡",
            "delivery.json",
            subscribes_to=["identity_&_attack_surface"],
        ),
    ]
