"""Build a LocalVectorStore from every markdown file in the docs/ folder."""
from __future__ import annotations

import pathlib

from .vectorstore import LocalVectorStore, chunk_markdown

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs"


def build_store() -> LocalVectorStore:
    store = LocalVectorStore()
    all_chunks = []
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        all_chunks.extend(chunk_markdown(md_file))
    store.index(all_chunks)
    return store


if __name__ == "__main__":
    s = build_store()
    demo = s.query("What is loop pipelining?")
    for hit in demo:
        print(f"[{hit['source']}] (distance={hit['distance']:.3f})")
        print(hit["text"][:200], "...\n")
