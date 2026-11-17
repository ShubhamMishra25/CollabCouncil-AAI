# CollabCouncil

CollabCouncil is a Streamlit decision command center that coordinates specialist
agents to produce evidence-backed launch recommendations. Agents research market
conditions, regulations, finances, competitors, and marketing strategy; share
findings through a common blackboard; negotiate conflicts; and synthesize a
traceable recommendation.

## What it includes

- Goal decomposition and specialist workstream assignment
- Market, regulatory, financial, competitive, and marketing specialists
- Shared blackboard communication and consistency checks
- Bounded conflict negotiation with configurable human escalation
- Traceable recommendations, risks, activity logs, and evidence
- Scenario, market, competitor, financial, regulatory, and internal-plan datasets
- A pluggable technology roster for software migration decisions
- Single-generalist comparison in the Streamlit interface

## Requirements

- Python 3.10 or newer
- A Groq API key for LLM-assisted extraction, follow-up questions, and
  recommendations. The application can use deterministic fallbacks for some
  operations when the key is not configured.

## Quick start

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file when using Groq:

```dotenv
GROQ_API_KEY=your-groq-api-key
# Optional overrides:
# GROQ_MODEL=openai/gpt-oss-120b
# MAX_ROUNDS=3
# AUTO_HUMAN=true
# AUTO_HUMAN_CHOICE=1
```

Start the application:

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, select a product and market, and run a
scenario. You can also ask a natural-language question such as:

> Should we launch NovaBand in Brazil next quarter?

## Repository layout

```text
app.py                         Streamlit user interface
src/orchestrator.py            Multi-agent coordination pipeline
src/agents/                    Specialist, negotiation, and synthesis agents
src/blackboard.py              Shared findings and event state
src/tools/                     Dataset access helpers
src/pluggable/                 Alternative specialist rosters
data/                          Default scenario datasets
test_data/                     Test fixture datasets
CollabCouncil_Fixed.ipynb      Notebook version of the project
```

## Configuration

Configuration is loaded from environment variables or `.env` by
`src/config.py`:

| Variable | Default | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | empty | Groq API credential |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Primary Groq model |
| `MAX_ROUNDS` | `3` | Maximum conflict-negotiation rounds |
| `AUTO_HUMAN` | `true` | Automatically apply the escalation choice |
| `AUTO_HUMAN_CHOICE` | `1` | Default escalation action |

Do not commit `.env` files or API keys.

## Data

The default datasets live in `data/`. The application discovers a compatible
data directory containing `market.csv`, so the fixture data can also be used
when developing or testing locally.

## Notebook

`CollabCouncil_Fixed.ipynb` contains a notebook-oriented version of the
collaborative agent workflow. In Google Colab, add `GROQ_API_KEY` through the
Secrets panel before running cells that call the Groq client.

## License

No license file is currently included in this repository.
