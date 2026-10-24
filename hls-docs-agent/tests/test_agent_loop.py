"""
Tests the agent's tool-call loop logic without hitting the real API, by
faking the two-turn shape a real Claude response takes: first a
tool_use turn, then a final text turn once tool results are supplied.
"""
import pathlib
import sys
import types
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import os
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")

from src.agent import DocsAgent


@dataclass
class FakeBlock:
    type: str
    text: str = ""
    name: str = ""
    input: dict = None
    id: str = ""


@dataclass
class FakeResponse:
    stop_reason: str
    content: list


class FakeMessages:
    """Returns a tool_use response once, then a final text response."""

    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return FakeResponse(
                stop_reason="tool_use",
                content=[
                    FakeBlock(
                        type="tool_use",
                        name="explain_synthesis_report",
                        input={"function_name": "fir_filter"},
                        id="tool_1",
                    )
                ],
            )
        return FakeResponse(
            stop_reason="end_turn",
            content=[FakeBlock(type="text", text="The fir_loop was not pipelined. [source: fir_filter_report.txt]")],
        )


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


def test_agent_ask_calls_synthesis_report_tool_then_returns_final_text(monkeypatch):
    agent = DocsAgent.__new__(DocsAgent)  # bypass __init__ (no real API client)
    agent.client = FakeClient()
    from src.ingest import build_store
    agent.store = build_store()

    answer = agent.ask("Why wasn't the fir_loop pipelined?")

    assert "fir_loop" in answer
    assert agent.client.messages.calls == 2


def test_run_tool_dispatches_to_search_docs():
    agent = DocsAgent.__new__(DocsAgent)
    from src.ingest import build_store
    agent.store = build_store()

    result = agent._run_tool("search_docs", {"query": "loop pipelining"})

    assert "hls_basics.md" in result


def test_run_tool_dispatches_to_explain_synthesis_report():
    agent = DocsAgent.__new__(DocsAgent)
    from src.ingest import build_store
    agent.store = build_store()

    result = agent._run_tool("explain_synthesis_report", {"function_name": "fir_filter"})

    assert "fir_filter" in result
    assert "DSP=3" in result


def test_run_tool_handles_unknown_report():
    agent = DocsAgent.__new__(DocsAgent)
    from src.ingest import build_store
    agent.store = build_store()

    result = agent._run_tool("explain_synthesis_report", {"function_name": "does_not_exist"})

    assert "No report found" in result


def test_run_tool_finds_report_when_given_a_loop_name():
    """Users ask about 'fir_loop' (a loop), but the report is filed as 'fir_filter'."""
    agent = DocsAgent.__new__(DocsAgent)
    from src.ingest import build_store
    agent.store = build_store()

    result = agent._run_tool("explain_synthesis_report", {"function_name": "fir_loop"})

    assert "Top function: fir_filter" in result
    assert "not pipelined" in result


def test_unknown_report_message_tells_model_to_retry():
    agent = DocsAgent.__new__(DocsAgent)
    from src.ingest import build_store
    agent.store = build_store()

    result = agent._run_tool("explain_synthesis_report", {"function_name": "nonexistent_xyz"})

    assert "No report found" in result
    assert "fir_filter" in result
    assert "Retry" in result
