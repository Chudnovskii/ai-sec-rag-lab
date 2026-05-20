"""Vector similarity retrieval over the documents tables."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .config import Config
from .db import connect
from .embed import embed_text


@dataclass(frozen=True)
class Retrieval:
    """One retrieved chunk plus its similairty score."""
    source_path: str
    content: str
    similarity: float # higher = closer match; range [0, 1] for cosine on normalized vectors

def retrieve(cfg: Config, tenant_id: str, query: str, k: int = 5) -> List[Retrieval]:
    """Return the top-k most similar chunks for this query within this tenant.

    The tenant filter is applied in SQL, not in Python. Chunks belonging
    to other tenants are never read into application memory.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if not query.strip():
        return []
    
    query_vec = embed_text(cfg, query)

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source_path,
                       content,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM documents
                WHERE tenant_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_vec, tenant_id, query_vec, k),
            )
            rows = cur.fetchall()

    return [
        Retrieval(source_path=row[0], content=row[1], similarity=float(row[2]))
        for row in rows
    ]