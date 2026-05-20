"""Configuration loaded from environment variables."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root into os.environ.
# Safe to call multiple times; later imports of this module are no-ops.
load_dotenv()

# PROJECT_ROOT resolves to the ai-sec-rag-lab/ directory regardless of where
# Python is invoked from. parents[2] climbs: config.py -> rag/ -> src/ -> root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    database_url: str
    chat_model: str = "claude-sonnet-4-5"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chunk_size_chars: int = 800
    chunk_overlap_chars: int = 100

    def __repr__(self) -> str:
        return (
            f"Config(anthropic_api_key={_redact(self.anthropic_api_key)}), "
            f"database_url={self.database_url!r}, "
            f"chat_model={self.chat_model!r}, "
            f"embedding_model={self.embedding_model!r}, "
            f"embedding_dim={self.embedding_dim}, "
            f"chunk_size_chars={self.chunk_size_chars}, "
            f"chunk_overlap_chars={self.chunk_overlap_chars})"
        )

def _redact(secret: str) -> str:
    """Show only the first 8 and last 4 chars of a secret. Length is hidden."""
    if not secret:
        return "<unset>"
    if len(secret) <= 12:
        return "<redacted>"
    return f"{secret[:8]}...{secret[-4:]}"


def load_config() -> Config:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    db_url = os.environ.get("DATABASE_URL")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set. Check your .env file.")
    return Config(anthropic_api_key=api_key, database_url=db_url)