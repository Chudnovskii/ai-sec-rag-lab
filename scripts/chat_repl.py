"""Interactive REPL for the Northwind RAG chatbot.

Usage:
    uv run python scripts/chat_reply.py

Commands inside the REPL:
    /tenant <id> switch tenant (engineering or hr)
    /tenant      show curren tenant
    /k <n>       set top-k retrieval (default 5)
    /raw         toggle showing the full retrieved chunks
    /help        show commands
    /exit        quit
"""
from __future__ import annotations

import sys
from pathlib import Path


# Allow running this script directly (python script/chat_repl.py)
# by adding the project root to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.config import load_config
from src.rag.chat import chat


VALID_TENANTS = {"engineering", "hr"}


def print_help() -> None:
    print("Commands:")
    print("  /tenant <id>   switch active tenant (engineering or hr)")
    print("  /tenant        show current tenant")
    print("  /k <n>         set top-k retrieval (default 5)")
    print("  /raw           toggle showing the full retrieved chunks")
    print("  /help          show this help")
    print("  /exit          quit")
    print()

def filename_of(source_path: str) -> str:
    """Get just the filename from a source path, robust to OS path separators."""
    return source_path.replace("\\", "/").rsplit("/", 1)[-1]

def main() -> int:
    cfg = load_config()
    tenant = "engineering"
    k = 5
    show_raw = False

    print(f"Northwind RAG REPL. Tenant: {tenant}. Top-k: {k}.")
    print("Type /help for commands, /exit to quit.\n")

    while True:
        try:
            line = input(f"[{tenant}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue

        if line.startswith("/"):
            parts = line.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/exit":
                return 0
            elif cmd == "/help":
                print_help()
            elif cmd == "/tenant":
                if not arg:
                    print(f"Current tenant: {tenant}\n")
                elif arg in VALID_TENANTS:
                    tenant = arg
                    print(f"Switched to tenant: {tenant}\n")
                else:
                    print(f"Unknown tenant {arg!r}. Valid: {sorted(VALID_TENANTS)}\n")
            elif cmd == "/k":
                try:
                    new_k = int(arg)
                    if new_k <= 0:
                        raise ValueError
                    k = new_k
                    print(f"Top-k set to {k}\n")
                except ValueError:
                    print("Usage: /k <positive integer>\n")
            elif cmd == "/raw":
                show_raw = not show_raw
                print(f"Show raw chunks: {show_raw}\n")
            else:
                print(f"Unknown command: {cmd}\n")
            continue

        # Anything else is a query.
        try:
            result = chat(cfg, tenant, line, k=k)
        except Exception as e:
            print(f"error: {type(e).__name__}: {e}\n")
            continue

        print()
        print("ANSWER:")
        print(result.answer)
        print()
        print("RETRIEVED:")
        for r in result.retrievals:
            print(f"  {r.similarity:.3f}  {filename_of(r.source_path)}")
            if show_raw:
                snippet = r.content.replace("\n", " ")[:200]
                print(f"          {snippet}...")
        print()


if __name__ == "__main__":
    sys.exit(main())