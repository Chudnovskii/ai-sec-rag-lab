# ai-sec-rag-lab

A multi-tenant retrieval-augmented chatbot built from raw primitives to study
LLM application security. Project 1 of a personal learning series pivoting
from traditional defensive security into AI security.

**Status:** mid-build. Application complete, attack phase upcoming.

## What this is

A Python application that:
- Ingests a synthetic multi-tenant document corpus (the fictional Northwind
  Robotics) into Postgres with the pgvector extension
- Embeds chunks using a local sentence-transformers model
- Retrieves tenant-scoped context for a user query
- Calls Claude to produce an answer grounded in the retrieved context

Built deliberately from raw API calls — no LangChain, no LlamaIndex — so
that every trust boundary in the system is visible and attackable.

## Why this exists

The project follows a "build, break, defend" arc:

1. **Build:** working RAG app with sensible default security posture
2. **Break:** systematic attacks against the threat model
3. **Defend:** layered mitigations, with honest measurement of residual risk

Threat model is in `docs/threat-model.md`.

## Running locally

```bash
# Prerequisites: Docker, Python 3.12+, uv, an Anthropic API key
cp .env.example .env
# edit .env with your ANTHROPIC_API_KEY

uv sync
docker compose up -d

uv run python -c "from src.rag.config import load_config; from src.rag.db import init_schema, seed_tenants; cfg = load_config(); init_schema(cfg); seed_tenants(cfg)"
uv run python -c "from src.rag.config import load_config; from src.rag.ingest import ingest; ingest(load_config())"
```

## Project layout

src/rag/         application code
data/corpus/     synthetic Northwind document corpus
docs/            threat model and (eventually) attack writeups
scripts/         one-off operational scripts

## Status of the build

- [x] Configuration with secret redaction
- [x] Postgres + pgvector schema
- [x] Local embedding pipeline
- [x] Multi-tenant ingestion with verified isolation
- [x] Tenant-scoped retrieval
- [x] Chat handler with grounded responses
- [x] Threat model
- [ ] Interactive REPL
- [ ] Attack tooling and break-phase writeups
- [ ] Defense layer and residual-risk measurement