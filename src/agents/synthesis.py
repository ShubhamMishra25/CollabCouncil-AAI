"""Agent 10: Traceable Recommendation Synthesis Engine."""

from typing import List, Dict, Any
from src.blackboard import Blackboard
from src.models import RecommendationClause, Finding


class TraceableSynthesisEngine:
    """Synthesizes cross-functional specialist findings into an auditable, clause-attributed executive recommendation."""

    @staticmethod
    def synthesize(bb: Blackboard) -> List[RecommendationClause]:
        """Produce structured clauses linking each executive directive directly to underlying agent findings."""
        reg = bb.get_finding_by_topic("regulatory_clearance")
        fin = bb.get_finding_by_topic("financial_margin")
        mkt = bb.get_finding_by_topic("market_demand")
        plan = bb.get_finding_by_topic("launch_timeline")
        comp = bb.get_finding_by_topic("competitive_landscape")

        clauses: List[RecommendationClause] = []

        # If standard Nova Devices launch domain specialists exist:
        if reg and fin and comp:
            # 1. Market Opportunity Clause
            if mkt:
                clauses.append(
                    RecommendationClause(
                        clause_text=f"Market opportunity validated: {mkt.claim}",
                        source_agents=[mkt.agent],
                        source_findings=[mkt.id],
                        supporting_numbers={
                            "demand_index": mkt.numbers.get("demand_index"),
                            "tam_usd": mkt.numbers.get("tam_usd"),
                            "growth_pct": mkt.numbers.get("growth_rate_pct"),
                        },
                    )
                )

            # 2. Regulatory & Timeline Clause
            clauses.append(
                RecommendationClause(
                    clause_text=(
                        f"Regulatory requirement '{reg.numbers.get('certification_name', 'Certification')}' "
                        f"incurs a statutory timeline adjustment of +{reg.numbers.get('expected_delay_weeks', 0)} weeks "
                        f"and ${reg.numbers.get('fee_usd', 0):,} in compliance fees."
                    ),
                    source_agents=[reg.agent],
                    source_findings=[reg.id],
                    supporting_numbers={
                        "delay_weeks": reg.numbers.get("expected_delay_weeks"),
                        "fee_usd": reg.numbers.get("fee_usd"),
                        "blocker": reg.numbers.get("blocker", False),
                    },
                )
            )

            # 3. Schedule Integration Clause
            if plan:
                clauses.append(
                    RecommendationClause(
                        clause_text=(
                            f"Marketing plan incorporates the +{reg.numbers.get('expected_delay_weeks', 0)}w timeline shift; "
                            f"GTM advertising commitment stands at ${plan.numbers.get('ad_committed_usd', 0):,}."
                        ),
                        source_agents=[plan.agent, reg.agent],
                        source_findings=[plan.id, reg.id],
                        supporting_numbers={
                            "target_lead_time_wks": plan.numbers.get("target_lead_time_weeks"),
                            "ad_committed_usd": plan.numbers.get("ad_committed_usd"),
                        },
                    )
                )

            # 4. Unit Economics & Viability Cap Clause
            clauses.append(
                RecommendationClause(
                    clause_text=(
                        f"Unit economics yield a landed unit cost of ${fin.numbers.get('landed_unit_cost', 0):.2f} "
                        f"with projected net margin of {fin.numbers.get('net_margin_pct', 0)}%. "
                        f"Viability preserved provided certification cost remains under ${fin.numbers.get('cert_cost_cap', 0):,}."
                    ),
                    source_agents=[fin.agent],
                    source_findings=[fin.id],
                    supporting_numbers={
                        "net_margin_pct": fin.numbers.get("net_margin_pct"),
                        "landed_unit_cost": fin.numbers.get("landed_unit_cost"),
                        "cert_cost_cap": fin.numbers.get("cert_cost_cap"),
                    },
                )
            )

            # 5. Executive Action Directive
            final_action = bb.decision_log[-1] if bb.decision_log else "Proceed standard"
            lead_sources = [comp.agent]
            if bb.conflicts:
                lead_sources.extend(bb.conflicts[-1].involved_agents)

            clauses.append(
                RecommendationClause(
                    clause_text=f"Executive Action: {final_action}",
                    source_agents=list(dict.fromkeys(lead_sources)),
                    source_findings=[comp.id, fin.id],
                    supporting_numbers={
                        "competitor_gap_wks": comp.numbers.get("weeks_to_fill_gap"),
                        "resolution_status": bb.conflicts[-1].status if bb.conflicts else "CONSENSUS",
                    },
                )
            )
            return clauses

        # Generic synthesis for pluggable specialist rosters
        latest_by_topic: Dict[str, Finding] = {}
        for f in bb.findings.values():
            latest_by_topic[f.topic] = f

        for f in latest_by_topic.values():
            clauses.append(
                RecommendationClause(
                    clause_text=f.claim,
                    source_agents=[f.agent],
                    source_findings=[f.id],
                    supporting_numbers=f.numbers,
                )
            )

        final_action = bb.decision_log[-1] if bb.decision_log else "Proceed per specialist consensus."
        all_agents = list(dict.fromkeys([f.agent for f in latest_by_topic.values()]))
        all_fids = [f.id for f in latest_by_topic.values()]

        clauses.append(
            RecommendationClause(
                clause_text=f"Executive Action: {final_action}",
                source_agents=all_agents,
                source_findings=all_fids,
                supporting_numbers={"status": bb.conflicts[-1].status if bb.conflicts else "CONSENSUS"},
            )
        )
        return clauses
