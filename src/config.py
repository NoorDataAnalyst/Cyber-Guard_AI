"""
Central configuration module for Cyberbullying Detection System.
Defines project paths, pretrained model names, signal thresholds,
RAG settings, and policy constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
EXAMPLES_DIR = DATA_DIR / "examples"
POLICY_DIR = DATA_DIR / "policy_docs"
INDEX_DIR = DATA_DIR / "faiss_indices"

# Data file paths
EXAMPLES_PATH = EXAMPLES_DIR / "example_bank.csv"
POLICY_PATH = POLICY_DIR / "policy_corpus.csv"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "cyberbullying.db")))

# Pretrained HuggingFace Model Identifiers
TOXICITY_MODEL_NAME = os.getenv("TOXICITY_MODEL_NAME", "unitary/toxic-bert")
EMOTION_MODEL_NAME = os.getenv("EMOTION_MODEL_NAME", "SamLowe/roberta-base-go_emotions")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Signal Layer Thresholds
TOXICITY_THRESHOLD = float(os.getenv("TOXICITY_THRESHOLD", "0.50"))
EMOTION_THRESHOLD = float(os.getenv("EMOTION_THRESHOLD", "0.30"))

# RAG & Context Retrieval Settings
CONTEXT_HISTORY_N = 5       # Retrieve last N messages from thread
RAG_TOP_K_EXAMPLES = 3      # Top-k similar examples from example bank
RAG_TOP_K_POLICY = 2        # Top-k policy snippets from legal/policy corpus

# LLM Reasoning Agent Settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-5-sonnet-20241022")

# Classification Categories (Locked)
CATEGORIES = [
    "direct",
    "indirect",
    "sarcastic",
    "identity_attack",
    "threat",
    "not_bullying",
]

# Severity Levels (Locked)
SEVERITY_LEVELS = ["none", "mild", "moderate", "severe"]

# Severity -> Action Mapping (Locked Business Logic)
SEVERITY_ACTION_MAP = {
    "none": "no action",
    "mild": "soft warning",
    "moderate": "mute sender",
    "severe": "block message",
}

# Legal & Disclaimer Text
LEGAL_DISCLAIMER = (
    "DISCLAIMER: This report is generated automatically for general informational "
    "and policy awareness purposes only, and does not constitute formal legal advice."
)


def ensure_directories_exist() -> None:
    """Ensure all required project directories exist on filesystem."""
    for directory in [DATA_DIR, RAW_DATA_DIR, EXAMPLES_DIR, POLICY_DIR, INDEX_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


# Guarantee directory presence on import
ensure_directories_exist()
