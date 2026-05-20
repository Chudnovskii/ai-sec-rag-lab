"""Coprus ingestion: Chunk markdown files and load them into Postgres"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .config import Config, CORPUS_DIR
from .db import connect
from .embed import embed_texts


@dataclass(frozen=True)
class Chunk:
    """One chunk ready for insertion."""
    tenant_id: str
    source_path: str
    content: str


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping fixed-size character windows
    
    Returns a list of chunk strings. The last chunk may be shorter than chunk_size. Empty input returns an empty list
    """
    if not text:
        return[]
    if chunk_size <= 0:
        raise ValueError("Chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")
    
    chunks: List[str] = []
    step = chunk_size - overlap
    start = 0 
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += step
    return chunks


def discover_corpus(corpus_dir: Path) -> List[tuple[str, Path]]:
    """Walk the corpus directory and return (tenant_id, file_path) pairs.
    
    Files under public/ are returned once for each tenant.
    Files under hr/ are returned only for the hr tenant.
    Other top-level directories are ignored with a warning.
    """
    if not corpus_dir.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")
    
    pairs: List[tuple[str, Path]] = []
    for child in sorted(corpus_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name == "public":
            for path in sorted(child.rglob("*.md")):
                pairs.append(("engineering", path))
                pairs.append(("hr", path))
        elif child.name == "hr":
            for path in sorted(child.rglob("*.md")):
                pairs.append(("hr", path))
        else:
            print(f"warn: ignoring unkown corpus subdir {child.name!r}")
    return pairs


def build_chunks(cfg: Config, pairs: Iterable[tuple[str, Pth]]) -> List[Chunk]:
    """Read each file, chunk it, and label every chunk with its tenant."""
    out: List[Chunk] = []
    for tenant_id, path in pairs:
        text = path.read_text(encoding="utf-8")
        for piece in chunk_text(text, cfg.chunk_size_chars, cfg.chunk_overlap_chars):
            out.append(Chunk(tenant_id=tenant_id, source_path=str(path), content=piece))
    return out


def ingest(cfg: Config) -> int:
    """Full ingestion pipeline. Idempotent: existing rows for the same
    (tenant_id, source_path) are deleted before fresh chunks are inserted.
    
    Returns the number of chunks written.
    """
    pairs = discover_corpus(CORPUS_DIR)
    chunks = build_chunks(cfg, pairs)
    if not chunks: 
        print("warn: no chunks built; corpus appears empty")
        return 0
    
    # Embed in one batch for speed. With 10 short docs this is a few hundred
    # chunks at most; comfortably fits in memory.
    texts = [c.content for c in chunks]
    print(f"embedding {len(texts)} chunks...")
    vectors = embed_texts(cfg, texts)

    # Group affected (tenant_id, source_path) pairs so we can clean before
    # inserting. Using a set means we issue one DELETE per unique pair.
    affected = {(c.tenant_id, c.source_path) for c in chunks}

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            for tenant_id, source_path in affected:
                cur.execute(
                    "DELETE FROM documents "
                    "WHERE tenant_id = %s AND source_path = %s",
                    (tenant_id, source_path),
                )
            cur.executemany(
                "INSERT INTO documents (tenant_id, source_path, content, embedding) "
                "VALUES (%s, %s, %s, %s)",
                [
                    (c.tenant_id, c.source_path, c.content, v)
                    for c, v in zip(chunks, vectors)
                ],
            )
        conn.commit()

    print(f"ingested {len(chunks)} chunks across {len(affected)} (tenant, source) pairs")
    return len(chunks)