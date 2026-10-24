"""
A minimal RAG agent built on Claude's tool-use (function calling).

The agent is given one tool, `search_docs`, backed by the local vector store.
Claude decides for itself whether and when to call it based on the user's
question, inspects the results, and can call it again (e.g. to refine the
query) before producing a final grounded answer. This is the same
tool-use/reasoning-loop pattern used by larger agent frameworks, kept small
enough to read end to end in one sitting.

Requires ANTHROPIC_API_KEY to be set (see .env.example).
"""
from __future__ import annotations

import os
import pathlib

from anthropic import Anthropic
from dotenv import load_dotenv

from .ingest import build_store
from .synthesis_report import find_report, load_report

load_dotenv()

MODEL = "claude-sonnet-4-6"
REPORTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "sample_reports"

SEARCH_TOOL = {
    "name": "search_docs",
    "description": (
        "Search the local HLS/EDA knowledge base for passages relevant to a "
        "query. Returns the most relevant chunks with their source file. "
        "Use this whenever the user asks something that might be answered "
        "by the documentation, rather than answering from general knowledge."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A focused search query, e.g. 'loop pipelining' or 'C/RTL mismatch causes'.",
            }
        },
        "required": ["query"],
    },
}

EXPLAIN_REPORT_TOOL = {
    "name": "explain_synthesis_report",
    "description": (
        "Load and summarize an HLS synthesis report for a given top-level "
        "function (e.g. 'fir_filter'). Returns latency, clock timing, and "
        "resource utilization (BRAM/DSP/FF/LUT) so the agent can answer "
        "questions about a specific synthesis run, such as why a loop "
        "wasn't pipelined or what's consuming the most resources."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "function_name": {
                "type": "string",
                "description": "The top-level function (e.g. 'fir_filter') or a loop/name inside it (e.g. 'fir_loop'); the tool finds the matching report.",
            }
        },
        "required": ["function_name"],
    },
}

SYSTEM_PROMPT = (
    "You are a documentation and synthesis-report assistant for a High-Level "
    "Synthesis (HLS) engineering team. Use search_docs to ground general "
    "questions about HLS/EDA concepts in the team's documentation, and use "
    "explain_synthesis_report when the user asks about a specific "
    "function's synthesis results (latency, timing, resource usage, why a "
    "loop did or didn't pipeline, etc.). Cite which source file or report "
    "each fact came from. If neither tool has the answer, say so plainly "
    "rather than guessing. If a tool says a report was not found and lists "
    "available reports, retry once with an available name before giving up."
)


class DocsAgent:
    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env "
                "and add your key, or export it in your shell."
            )
        self.client = Anthropic(api_key=api_key)
        self.store = build_store()

    def _run_tool(self, name: str, tool_input: dict) -> str:
        if name == "search_docs":
            hits = self.store.query(tool_input["query"], n_results=3)
            if not hits:
                return "No relevant passages found."
            return "\n\n".join(f"[source: {h['source']}]\n{h['text']}" for h in hits)

        if name == "explain_synthesis_report":
            fn_name = tool_input["function_name"]
            report_path = find_report(fn_name, REPORTS_DIR)
            if report_path is None:
                available = [p.stem.replace("_report", "") for p in REPORTS_DIR.glob("*_report.txt")]
                return (
                    f"No report found for '{fn_name}'. Available reports: {available}. "
                    "Retry with one of the available names."
                )
            report = load_report(report_path)
            return report.as_context_string()

        return f"Unknown tool: {name}"

    def ask(self, question: str, max_turns: int = 5) -> str:
        messages = [{"role": "user", "content": question}]

        for _ in range(max_turns):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=[SEARCH_TOOL, EXPLAIN_REPORT_TOOL],
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                # Final answer: concatenate any text blocks.
                return "".join(
                    block.text for block in response.content if block.type == "text"
                )

            # Model wants to call a tool. Append its turn, run every
            # tool_use block, and feed the results back as a user turn.
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result_text = self._run_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})

        return "Reached max turns without a final answer."
