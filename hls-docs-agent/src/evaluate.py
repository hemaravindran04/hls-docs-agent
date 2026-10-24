"""
Small retrieval evaluation for the local vector store.

For each question in eval/questions.json we check whether the chunk we expect
(identified by its source file) appears in the top-k retrieved results.

Reported metrics:
  recall@1  - the expected source is the top result
  recall@3  - the expected source is within the top 3 results

IMPORTANT LIMITS (also stated in the README):
  * The questions were written by the project author against the same three
    small notes files, so this is a sanity check, not a benchmark.
  * 'paraphrase' questions deliberately avoid the notes' vocabulary to show
    the weakness of TF-IDF (keyword matching, not meaning).
"""
from __future__ import annotations

import json
import pathlib
from collections import defaultdict

from .ingest import build_store

QUESTIONS = pathlib.Path(__file__).resolve().parent.parent / "eval" / "questions.json"


def evaluate(k: int = 3) -> dict:
    store = build_store()
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "r1": 0, "rk": 0})
    misses = []

    for item in items:
        hits = store.query(item["q"], n_results=k)
        sources = [h["source"] for h in hits]
        bucket = stats[item["type"]]
        bucket["n"] += 1
        if sources and sources[0] == item["expected"]:
            bucket["r1"] += 1
        if item["expected"] in sources:
            bucket["rk"] += 1
        else:
            misses.append((item["q"], item["expected"], sources))

    total = {"n": 0, "r1": 0, "rk": 0}
    for b in stats.values():
        for key in total:
            total[key] += b[key]
    stats["all"] = total
    return {"k": k, "stats": dict(stats), "misses": misses}


def main() -> None:
    result = evaluate()
    k = result["k"]
    print(f"{'subset':<12}{'n':>4}{'recall@1':>10}{'recall@' + str(k):>10}")
    for name, b in result["stats"].items():
        print(f"{name:<12}{b['n']:>4}{b['r1'] / b['n']:>10.0%}{b['rk'] / b['n']:>10.0%}")
    if result["misses"]:
        print("\nMissed (expected source not in top-k):")
        for q, exp, got in result["misses"]:
            print(f"- {q!r}\n    expected {exp}, got {got}")


if __name__ == "__main__":
    main()
