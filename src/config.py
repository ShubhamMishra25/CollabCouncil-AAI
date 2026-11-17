"""Configuration settings for CollabCouncil."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Dynamically locate data directory
POSSIBLE_DATA_DIRS = [
    BASE_DIR / "data",
    BASE_DIR / "test_data" / "test_data",
    BASE_DIR / "test_data",
]

DATA_DIR = BASE_DIR / "data"
for p in POSSIBLE_DATA_DIRS:
    if p.exists() and (p / "market.csv").exists():
        DATA_DIR = p
        break

# API & LLM Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODEL = "qwen/qwen3.8-27b"

# Orchestrator & Negotiation Defaults
DEFAULT_MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "3"))
DEFAULT_AUTO_HUMAN = os.getenv("AUTO_HUMAN", "true").lower() in ("true", "1", "yes")
DEFAULT_HUMAN_CHOICE = int(os.getenv("AUTO_HUMAN_CHOICE", "1"))
