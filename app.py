"""Streamlit command center for the CollabCouncil decision engine."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.escalation import HumanEscalationAgent
from src.comparison import get_comparison_matrix
from src.config import DATA_DIR, GROQ_API_KEY
from src.orchestrator import CollabCouncilOrchestrator


st.set_page_config(
    page_title="CollabCouncil | Decision Command Center",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
    [data-testid="stMetric"] { background: #f7f9fc; border: 1px solid #e8edf5; padding: 14px; border-radius: 12px; }
    .hero { padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg,#102a43,#176b87); color: white; margin-bottom: 1rem; }
    .hero h1 { margin: 0; font-size: 2.2rem; }
    .hero p { margin: .35rem 0 0; opacity: .84; font-size: 1.05rem; }
    .finding { border: 1px solid #e5eaf1; border-radius: 12px; padding: 1rem; margin-bottom: .7rem; background: white; }
    .finding small { color: #64748b; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_scenarios() -> List[Dict[str, Any]]:
    with (DATA_DIR / "scenarios.json").open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_market() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "market.csv")


@st.cache_data
def load_competitors() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "competitors.csv")


def money(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def parse_question(question: str, products: List[str], countries: List[str]) -> tuple[str, str]:
    """Resolve a natural-language question to a supported product and market."""
    normalized = question.lower()
    product = next((item for item in products if item.lower() in normalized), None)
    country = next((item for item in countries if item.lower() in normalized), None)
    if not product or not country:
        raise ValueError(
            "Please mention one supported product and market, such as "
            "'Should we launch NovaBand in Brazil next quarter?'"
        )
    return product, country


def run_council(product: str, country: str, selected_option: int) -> None:
    progress = st.progress(0, text="Initializing council…")
    events: List[Any] = []

    def on_event(phase: str, agent: str, icon: str, action: str, detail: str) -> None:
        events.append((phase, agent, icon, action, detail))
        progress.progress(min(98, 8 + len(events) * 5), text=f"{icon} {action}")

    try:
        council = CollabCouncilOrchestrator(
            goal_product=product,
            goal_country=country,
            on_event=on_event,
            auto_human=True,
            human_choice=selected_option,
        )
        clauses = council.run_pipeline()
        st.session_state.result = {
            "council": council,
            "clauses": clauses,
            "events": events,
            "product": product,
            "country": country,
        }
        progress.progress(100, text="Council complete")
    except Exception as error:
        progress.empty()
        st.error(f"Council run failed: {error}")
        st.session_state.pop("result", None)


def render_overview(result: Dict[str, Any], scenario: Dict[str, Any]) -> None:
    council = result["council"]
    findings = list(council.bb.findings.values())
    conflict = council.bb.conflicts[-1] if council.bb.conflicts else None
    fin = council.bb.get_finding_by_topic("financial_margin")
    reg = council.bb.get_finding_by_topic("regulatory_clearance")

    cols = st.columns(4)
    cols[0].metric("Decision", (conflict.status if conflict else "CONSENSUS").title())
    cols[1].metric("12-month profit", money(scenario.get("profit_12m_usd")))
    cols[2].metric("Regulatory delay", f"{reg.numbers.get('expected_delay_weeks', 0)} weeks" if reg else "—")
    cols[3].metric("Net margin", f"{fin.numbers.get('net_margin_pct', 0)}%" if fin else "—")

    if scenario.get("headline"):
        st.info(f"**Scenario signal:** {scenario['headline']}")
    if council.bb.decision_log:
        st.success(f"**Executive direction:** {council.bb.decision_log[-1]}")

    st.subheader("Specialist snapshot")
    cards = st.columns(len(findings) or 1)
    for card, finding in zip(cards, findings):
        card.markdown(
            f'<div class="finding"><small>{finding.agent}</small><br>'
            f'<b>{finding.topic.replace("_", " ").title()}</b><br>'
            f'{finding.claim}</div>',
            unsafe_allow_html=True,
        )


def render_recommendation(result: Dict[str, Any]) -> None:
    st.subheader("Traceable recommendation")
    st.caption("Every directive is linked to the finding IDs and agents that support it.")
    for index, clause in enumerate(result["clauses"], 1):
        with st.container(border=True):
            st.markdown(f"**{index}. {clause.clause_text}**")
            st.caption(
                f"Sources: {', '.join(clause.source_agents)} · "
                f"Findings: {', '.join(clause.source_findings)}"
            )
            if clause.supporting_numbers:
                st.json(clause.supporting_numbers, expanded=False)


def render_risk(result: Dict[str, Any]) -> None:
    council = result["council"]
    conflict = council.bb.conflicts[-1] if council.bb.conflicts else None
    if not conflict:
        st.success("No cross-functional conflicts detected. The council reached consensus.")
        return

    status_color = {"RESOLVED": "success", "ESCALATED": "warning", "UNRESOLVED": "error"}.get(
        conflict.status, "info"
    )
    getattr(st, status_color)(f"**{conflict.status}** · {conflict.issue}")
    st.write(conflict.resolution_details)
    st.metric("Negotiation rounds", conflict.rounds_run)
    if conflict.hard_constraints_violated:
        st.warning("Constraints: " + " · ".join(conflict.hard_constraints_violated))
    if conflict.negotiation_history:
        st.dataframe(pd.json_normalize(conflict.negotiation_history), use_container_width=True, hide_index=True)

    if conflict.status == "ESCALATED":
        dossier = HumanEscalationAgent.prepare_dossier(council.bb)
        with st.expander("Executive escalation dossier"):
            st.json(dossier, expanded=False)


def render_activity(result: Dict[str, Any]) -> None:
    council = result["council"]
    logs = council.bb.execution_logs
    if not logs:
        st.info("No activity recorded yet.")
        return
    frame = pd.DataFrame(
        [
            {"Phase": item.phase, "Agent": f"{item.icon} {item.agent}", "Action": item.action, "Detail": item.detail}
            for item in logs
        ]
    )
    phases = frame["Phase"].value_counts().rename_axis("Phase").reset_index(name="Events")
    left, right = st.columns([1, 2])
    left.plotly_chart(px.bar(phases, x="Phase", y="Events", color="Events"), use_container_width=True)
    right.dataframe(frame, use_container_width=True, hide_index=True)


st.markdown(
    '<div class="hero"><h1>🧭 CollabCouncil</h1>'
    '<p>Multi-agent launch decisions with evidence, negotiation, and executive traceability.</p></div>',
    unsafe_allow_html=True,
)

scenarios = load_scenarios()
products = sorted({item["product"] for item in scenarios})
countries = sorted({item["country"] for item in scenarios})
scenario_map = {(item["product"], item["country"]): item for item in scenarios}

with st.sidebar:
    st.header("Optional controls")
    product = st.selectbox("Product", products, index=products.index("NovaBand") if "NovaBand" in products else 0)
    country = st.selectbox("Market", countries, index=countries.index("Brazil") if "Brazil" in countries else 0)
    scenario = scenario_map[(product, country)]
    st.divider()
    st.caption("Choose an escalation action if the council cannot negotiate a viable compromise.")
    escalation = st.selectbox(
        "Human escalation directive",
        options=[1, 2, 3],
        format_func=lambda value: {
            1: "Abort launch",
            2: "Strategic loss-leader",
            3: "Expedited compliance budget",
        }[value],
    )
    if not GROQ_API_KEY:
        st.warning("No GROQ_API_KEY detected. The council will use deterministic fallbacks where needed.")
    if st.button("Run selected scenario", use_container_width=True):
        run_council(product, country, escalation)
    st.divider()
    st.caption("Data sources")
    st.write("Market, competitor, regulatory, financial, and internal planning datasets")

st.markdown("## Ask the council")
st.caption(
    "Describe the decision in plain English. The council will decompose your goal, "
    "consult its specialists, negotiate conflicts, and return one evidence-backed recommendation."
)

with st.form("ask_council_form", clear_on_submit=False):
    question = st.text_area(
        "Your question",
        value=st.session_state.get("question", ""),
        height=92,
        placeholder="Should we launch NovaBand in Brazil next quarter?",
        label_visibility="collapsed",
    )
    ask = st.form_submit_button("🧭 Ask the council", type="primary", use_container_width=True)

if ask:
    try:
        asked_product, asked_country = parse_question(question, products, countries)
        st.session_state.question = question
        st.session_state.chat_history = st.session_state.get("chat_history", []) + [
            {"question": question, "product": asked_product, "country": asked_country}
        ]
        run_council(asked_product, asked_country, escalation)
        product, country = asked_product, asked_country
        scenario = scenario_map[(product, country)]
    except ValueError as error:
        st.error(str(error))

with st.expander("Try a question", expanded=not bool(st.session_state.get("result"))):
    examples = [
        "Should we launch NovaBand in Brazil next quarter?",
        "Is NovaAir in India financially viable despite regulatory delays?",
        "Can NovaBuds enter Germany before competitors fill the gap?",
    ]
    st.write(" · ".join(f"`{example}`" for example in examples))

if st.session_state.get("chat_history"):
    st.caption("Recent questions")
    st.dataframe(
        pd.DataFrame(
            [
                {"Question": item["question"], "Resolved goal": f"{item['product']} in {item['country']}"}
                for item in st.session_state.chat_history[-5:]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

result = st.session_state.get("result")
if result:
    product, country = result["product"], result["country"]
scenario = scenario_map[(product, country)]
if result and (result["product"], result["country"]) != (product, country):
    st.info("The displayed result belongs to a different scenario. Run the council to refresh it.")
    result = None

if result:
    render_overview(result, scenario)
    tabs = st.tabs(["Recommendation", "Risks & negotiation", "Activity stream", "Data explorer", "System comparison"])
    with tabs[0]:
        render_recommendation(result)
    with tabs[1]:
        render_risk(result)
    with tabs[2]:
        render_activity(result)
    with tabs[3]:
        market = load_market()
        competitors = load_competitors()
        st.subheader("Market context")
        st.dataframe(market[market["country"] == country], use_container_width=True, hide_index=True)
        st.subheader("Competitive context")
        st.dataframe(
            competitors[(competitors["country"] == country) & (competitors["product"] == product)],
            use_container_width=True,
            hide_index=True,
        )
    with tabs[4]:
        st.subheader("Why a council?")
        st.dataframe(get_comparison_matrix(), use_container_width=True, hide_index=True)
else:
    st.info("👈 Select a product and market, then click **Run council** to begin.")
    preview = pd.DataFrame(
        [
            {
                "Product": item["product"],
                "Market": item["country"],
                "Outcome": item["expected_outcome"],
                "12-month profit": money(item["profit_12m_usd"]),
                "Delay": f"{item['expected_delay_weeks']} weeks",
            }
            for item in scenarios
        ]
    )
    st.subheader("Scenario portfolio")
    st.dataframe(preview, use_container_width=True, hide_index=True)
