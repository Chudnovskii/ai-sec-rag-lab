"""Postgres connection and schema for the RAG lab."""
from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector

from .config import Config


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS tenants (
    id            text PRIMARY KEY,
    display_name  text NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id            bigserial PRIMARY KEY,
    tenant_id     text NOT NULL REFERENCES tenants(id),
    source_path   text NOT NULL,
    content       text NOT NULL,
    embedding     vector(384) NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS documents_tenant_idx
    ON documents (tenant_id);

CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING hnsw (embedding vector_cosine_ops)
"""

@contextmanager
def connect(cfg: Config, *, register_types: bool = True) -> Iterator[psycopg.Connection]:
    """Yield a Postgres connection.

    register_types=True (default) registers pgvector type adapters so Python
    lists round-trip cleanly to/from vector columns. Set to False for the
    very first connection that creates the extension itself, since the
    type doesn't exist until then.
    """
    with psycopg.connect(cfg.database_url) as conn:
        if register_types:
            register_vector(conn)
        yield conn


def init_schema(cfg: Config) -> None:
    """Create the pgvector extension and our tables. Idempotent."""
    with connect(cfg, register_types=False) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()

def seed_tenants(cfg: Config) -> None:
    """Insert the two tenants we use throughout the lab. Idempotent"""
    with connect(cfg) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO tenants (id, display_name) VALUES (%s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                [
                    ("engineering", "Engineering"),
                    ("hr", "Human Resources"),
                ],
            )
        conn.commit()