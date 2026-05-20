"""Embedding model loading and inference."""
from __future__ import annotations

from typing import List, Sequence

from sentence_transformers import SentenceTransformer

from .config import Config

# Module-level cache. The first call to get_model() loads the weights;
# Subsequent calls return the same instance. Loading takes a few seconds
# on first use because the weights download from Hugging Face.
_model: SentenceTransformer | None = None

def get_model(cfg: Config) -> SentenceTransformer:
    """Return a loaded embedding model, caching it on the module."""
    global _model
    if _model is None:
        _model = SentenceTransformer(cfg.embedding_model)
    return _model


def embed_texts(cfg: Config, texts: Sequence[str]) -> List[List[float]]:
    """Embed a batch of texts. Returns one vector per input text.
    Always batched even if you have one input - the model is much faster
    on batches because of internal vectorization. We always pass a list.
    """
    if not texts:
        return []
    model = get_model(cfg)
    embeddings = model.encode(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    # encode() returns a numpy array; convert to plain Python lists for
    # clean handoff to pgvector and JSON-friendly logging.
    return embeddings.tolist()


def embed_text(cfg: Config, text: str) -> List[float]:
    """Embed a single text. Convenienve wrapper around embed_texts."""
    return embed_texts(cfg, [text])[0]
