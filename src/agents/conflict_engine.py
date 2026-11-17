"""Agent 7: Conflict Detection & Structured Negotiation Engine."""

import json
from typing import Dict, Any, List, Optional
from src.blackboard import Blackboard
from src.models import ConflictRecord
from src.tools.financial_tool import FinancialTool
from src.llm import llm
from src.config import DEFAULT_MAX_ROUNDS


class ConflictNegotiationEngine:
    """Detects multi-agent goal divergence, facilitates iterative LLM negotiation, and validates mathematical concessions."""

    def __init__(self, max_rounds: int = DEFAULT_MAX_ROUNDS):
        self.max_rounds = max_rounds

    def detect_conflicts(self, bb: Blackboard) -> List[str]:
        """Detect direct conflicts between specialist findings and operational constraints."""
        conflicts = []
        reg_f = bb.get_finding_by_topic("regulatory_clearance")
        plan_f = bb.get_finding_by_topic("launch_timeline")
        fin_f = bb.get_finding_by_topic("financial_margin")
        comp_f = bb.get_finding_by_topic("competitive_landscape")

        # 1. Direct Regulatory Blocker
        if reg_f and reg_f.numbers.get("blocker", False):
            conflicts.append("Hard Statutory Blocker: Import permits permanently denied.")

        # 2. Schedule Mismatch: Target vs Regulatory delay
        target_wks = bb.constraints.get("target_lead_time_weeks", 8)
        base_delay = reg_f.numbers.get("expected_delay_weeks", 0) if reg_f else 0
        if base_delay > target_wks:
            conflicts.append(
                f"Schedule Clash: Marketing target is {target_wks} weeks, but statutory compliance requires {base_delay} weeks."
            )

        # 3. Unit Economics Viability
        if fin_f and not fin_f.numbers.get("is_net_positive", True):
            conflicts.append(
                f"Margin Deficit: Landed and fixed costs produce negative net margin ({fin_f.numbers.get('net_margin_pct')}%%)."
            )

        # 4. Competitive Preemption
        if comp_f and reg_f:
            comp_window = comp_f.numbers.get("weeks_to_fill_gap", 99)
            if base_delay >= comp_window:
                conflicts.append(
                    f"Competitive Preemption: {comp_f.numbers.get('primary_rival')} will capture segment in {comp_window} weeks (our delay is {base_delay} weeks)."
                )

        return conflicts

    def negotiate(self, bb: Blackboard) -> str:
        """Run bounded multi-round negotiation between affected specialist agents."""
        conflicts_found = self.detect_conflicts(bb)

        if not conflicts_found:
            bb.log_event(
                phase="Conflict Resolution",
                agent="Conflict Detection & Negotiation Agent",
                icon="✅",
                action="No Conflict Detected",
                detail="All specialist constraints and margins align with targets.",
                level="SUCCESS",
            )
            bb.decision_log.append("Consensus Achieved: Proceed with standard go-to-market plan.")
            return "NO_CONFLICT"

        # Check for absolute statutory blockers
        reg_f = bb.get_finding_by_topic("regulatory_clearance")
        if reg_f and reg_f.numbers.get("blocker", False):
            reason = reg_f.numbers.get("reason", "Statutory ban")
            rec = ConflictRecord(
                conflict_id="CONF_STATUTORY_BLOCKER",
                issue=f"Statutory Blocker: {reason}",
                involved_agents=["Regulatory & Compliance Specialist"],
                hard_constraints_violated=["Legal Clearance"],
                rounds_run=1,
                status="UNRESOLVED",
                resolution_details=f"Unresolvable legal blocker: {reason}.",
            )
            bb.conflicts.append(rec)
            bb.log_event(
                phase="Conflict Resolution",
                agent="Conflict Detection & Negotiation Agent",
                icon="🚫",
                action="Statutory Blocker",
                detail=rec.issue,
                level="ERROR",
            )
            return "UNRESOLVED"

        fin_f = bb.get_finding_by_topic("financial_margin")
        comp_f = bb.get_finding_by_topic("competitive_landscape")

        p = bb.goal.get("product", "Unknown")
        c = bb.goal.get("country", "Unknown")
        cert_cost = float(reg_f.numbers.get("fee_usd", 0.0)) if reg_f else 0.0
        base_delay = int(reg_f.numbers.get("expected_delay_weeks", 0)) if reg_f else 0
        comp_window = int(comp_f.numbers.get("weeks_to_fill_gap", 99)) if comp_f else 99

        bb.log_event(
            phase="Conflict Resolution",
            agent="Conflict Detection & Negotiation Agent",
            icon="⚡",
            action="Conflicts Detected",
            detail=" | ".join(conflicts_found),
            level="WARNING",
        )

        negotiation_history = []

        # Multi-round negotiation loop
        for round_num in range(1, self.max_rounds + 1):
            system_instruction = (
                "You are the Mediator in a collaborative multi-agent council. "
                "The Council faces conflicts between launch timelines, financial margins, and competitor threat windows. "
                "Propose strategic concessions to achieve a viable compromise. "
                "Return strictly valid JSON with keys:\n"
                "  - 'rationale': string explaining the compromise\n"
                "  - 'price_adjustment_usd': float (0.0 to 30.0)\n"
                "  - 'fixed_cost_reduction_usd': float (0.0 to 15000.0)\n"
                "  - 'soft_launch_allowed': boolean\n"
                "  - 'pre_order_bridge': boolean (pre-orders preserve market share against rival)"
            )

            prompt = (
                f"Round {round_num}/{self.max_rounds}\n"
                f"Product: {p}, Country: {c}\n"
                f"Issues: {json.dumps(conflicts_found)}\n"
                f"Current Metrics: Landed cost: ${fin_f.numbers.get('landed_unit_cost') if fin_f else 0}, "
                f"Net Margin: {fin_f.numbers.get('net_margin_pct') if fin_f else 0}%, "
                f"Delay: {base_delay} weeks, Competitor Window: {comp_window} weeks.\n"
                f"Prior Round Failures: {json.dumps(negotiation_history)}"
            )

            try:
                raw_proposal = llm(system_instruction, prompt, json_mode=True)
                proposal = json.loads(raw_proposal)
            except Exception:
                proposal = {
                    "rationale": f"Default fallback compromise in round {round_num}",
                    "price_adjustment_usd": round(round_num * 5.0, 2),
                    "fixed_cost_reduction_usd": round(round_num * 4000.0, 2),
                    "soft_launch_allowed": True,
                    "pre_order_bridge": True,
                }

            price_adj = float(proposal.get("price_adjustment_usd", 0.0))
            cost_red = float(proposal.get("fixed_cost_reduction_usd", 0.0))
            pre_order_bridge = bool(proposal.get("pre_order_bridge", False))

            # Deterministically evaluate whether proposal satisfies constraints
            f_test = FinancialTool.calculate_margin(
                product=p,
                country=c,
                cert_cost=cert_cost,
                timeline_delay_weeks=base_delay,
                price_adjustment_usd=price_adj,
                fixed_cost_reduction_usd=cost_red,
            )

            fin_safe = f_test.get("is_net_positive", False)
            effective_comp_window = comp_window + (4 if pre_order_bridge else 0)
            comp_safe = base_delay <= effective_comp_window

            if fin_safe and comp_safe:
                # Compromise achieved
                bb.constraints["price_adjustment_usd"] = price_adj
                bb.constraints["fixed_cost_reduction_usd"] = cost_red
                bb.constraints["timeline_shift_weeks"] = base_delay
                bb.assumptions_version += 1

                res_details = (
                    f"Proceed with launch (+{base_delay}w regulatory schedule), retail price +${price_adj:.2f}, "
                    f"GTM overhead trimmed by ${cost_red:,.0f}"
                    f"{', with pre-order bridge' if pre_order_bridge else ''} (Net margin: {f_test['net_margin_pct']}%)."
                )

                rec = ConflictRecord(
                    conflict_id=f"CONF_RESOLVED_R{round_num}",
                    issue=conflicts_found[0],
                    involved_agents=[
                        "Regulatory & Compliance Specialist",
                        "Marketing & Planning Specialist",
                        "Financial Modeling Specialist",
                        "Competitive Intelligence Specialist",
                    ],
                    hard_constraints_violated=[],
                    rounds_run=round_num,
                    status="RESOLVED",
                    resolution_details=res_details,
                    negotiation_history=negotiation_history + [{"round": round_num, "proposal": proposal, "status": "ACCEPTED"}],
                )
                bb.conflicts.append(rec)
                bb.decision_log.append(f"Negotiated Compromise: {res_details}")

                bb.log_event(
                    phase="Conflict Resolution",
                    agent="Conflict Detection & Negotiation Agent",
                    icon="🤝",
                    action=f"Negotiation Converged (Round {round_num})",
                    detail=res_details,
                    level="SUCCESS",
                )
                return "RESOLVED"
            else:
                fail_reasons = []
                if not fin_safe:
                    fail_reasons.append(f"negative net margin ({f_test.get('net_margin_pct')}%)")
                if not comp_safe:
                    fail_reasons.append(f"competitor pre-emption ({base_delay}w > {effective_comp_window}w)")
                reason_str = " & ".join(fail_reasons)
                negotiation_history.append({
                    "round": round_num,
                    "proposal": proposal,
                    "price_adj": price_adj,
                    "cost_red": cost_red,
                    "rejected_due_to": reason_str,
                })

                bb.log_event(
                    phase="Conflict Resolution",
                    agent="Conflict Detection & Negotiation Agent",
                    icon="🔁",
                    action=f"Round {round_num} Rejected",
                    detail=f"Mediator proposed +${price_adj} price, -${cost_red} cost -> Failed: {reason_str}",
                    level="INFO",
                )

        # If loop finishes without resolution: Deadlock reached
        violated = []
        if fin_f and not fin_f.numbers.get("is_net_positive", True):
            violated.append("Net Margin > 0")
        if base_delay > comp_window:
            violated.append(f"Launch Delay ({base_delay}w) <= Competitor Window ({comp_window}w)")

        rec = ConflictRecord(
            conflict_id="CONF_UNRESOLVED",
            issue="Irreconcilable margin deficit and/or competitor preemption",
            involved_agents=[
                "Regulatory & Compliance Specialist",
                "Competitive Intelligence Specialist",
                "Financial Modeling Specialist",
            ],
            hard_constraints_violated=violated or ["Joint Feasibility Constraint"],
            rounds_run=self.max_rounds,
            status="UNRESOLVED",
            resolution_details="Hard constraint deadlock after bounded negotiation rounds.",
            negotiation_history=negotiation_history,
        )
        bb.conflicts.append(rec)

        bb.log_event(
            phase="Conflict Resolution",
            agent="Conflict Detection & Negotiation Agent",
            icon="⚠️",
            action="Negotiation Deadlock",
            detail=f"Failed to converge after {self.max_rounds} rounds. Escalation required.",
            level="WARNING",
        )
        return "UNRESOLVED"
