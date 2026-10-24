"""
A small local vector store for retrieval-augmented generation (RAG).

Design notes
------------
Rather than depending on a hosted embedding API or downloading a model at
runtime, this uses scikit-learn's TF-IDF vectorizer to turn each document
chunk into a sparse vector, then stores those vectors in Chroma (which is
happy to accept pre-computed embeddings instead of using its own embedding
function). This keeps the project fully offline/local except for the actual
LLM call, and keeps the moving parts easy to reason about and test.

For a production system you'd likely swap TF-IDF for a proper sentence
embedding model, but the retrieval *interface* — chunk, embed, store, query
by cosine similarity — is the same either way, which is the part worth
demonstrating here.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass

import chromadb
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class Chunk:
    id: str
    text: str
    source: str


def chunk_markdown(path: pathlib.Path, max_chars: int = 800) -> list[Chunk]:
    """Split a markdown file into paragraph-sized chunks.

    Splits on blank lines first (so we don't cut mid-paragraph), then packs
    consecutive paragraphs together up to `max_chars` so chunks stay a
    reasonable size for retrieval without being too fragmented.
    """
    text = path.read_text(encoding="utf-8")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[Chunk] = []
    buf = ""
    idx = 0
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) > max_chars and buf:
            chunks.append(Chunk(id=f"{path.stem}-{idx}", text=buf, source=path.name))
            idx += 1
            buf = para
        else:
            buf = candidate
    if buf:
        chunks.append(Chunk(id=f"{path.stem}-{idx}", text=buf, source=path.name))
    return chunks


class LocalVectorStore:
    """Wraps a Chroma collection with TF-IDF embeddings computed locally."""

    def __init__(self, collection_name: str = "hls_docs"):
        self._client = chromadb.Client()
        # Fresh in-memory collection each run keeps the demo simple and
        # avoids stale state between ingest calls.
        try:
            self._client.delete_collection(collection_name)
        except Exception:
            pass
        self._collection = self._client.create_collection(collection_name)
        self._vectorizer: TfidfVectorizer | None = None

    def index(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise ValueError("No chunks to index.")
        texts = [c.text for c in chunks]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        matrix = self._vectorizer.fit_transform(texts)
        embeddings = matrix.toarray().tolist()

        self._collection.add(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[{"source": c.source} for c in chunks],
        )

    def query(self, question: str, n_results: int = 3) -> list[dict]:
        if self._vectorizer is None:
            raise RuntimeError("Call index() before query().")
        query_vec = self._vectorizer.transform([question]).toarray().tolist()
        result = self._collection.query(query_embeddings=query_vec, n_results=n_results)

        hits = []
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            hits.append({"text": doc, "source": meta["source"], "distance": dist})
        return hits
