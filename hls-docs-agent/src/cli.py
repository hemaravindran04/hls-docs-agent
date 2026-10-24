"""Interactive CLI: ask questions about the local HLS/EDA docs."""
from __future__ import annotations

from .agent import DocsAgent


def main() -> None:
    print("HLS Docs Agent — ask a question, or type 'quit' to exit.\n")
    agent = DocsAgent()
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question or question.lower() in {"quit", "exit"}:
            break
        answer = agent.ask(question)
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
