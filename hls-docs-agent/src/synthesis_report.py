"""
Parses a text-based HLS synthesis report into a structured summary.

Real HLS tools (Vitis HLS, Bambu, etc.) emit a report with this general
shape: a timing/latency section and a resource utilization table. This
parser is intentionally tolerant of minor formatting differences (extra
whitespace, slightly different column widths) since report formatting
varies across tool versions.

To use this with a REAL report instead of the bundled sample: run your
own HLS synthesis, copy the generated report (e.g. Vitis HLS's
`<top-function>_csynth.rpt`) into `sample_reports/`, and point
`load_report()` at it.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field


@dataclass
class SynthesisReport:
    top_function: str
    target_clock_ns: float | None
    estimated_clock_ns: float | None
    latency_cycles: str | None
    latency_ns: float | None
    resources: dict[str, dict[str, str]] = field(default_factory=dict)
    utilization_pct: dict[str, str] = field(default_factory=dict)
    loop_notes: list[str] = field(default_factory=list)
    raw_text: str = ""

    def as_context_string(self) -> str:
        """A compact, LLM-friendly summary of the report's key facts."""
        lines = [f"Top function: {self.top_function}"]
        if self.target_clock_ns is not None:
            lines.append(f"Target clock period: {self.target_clock_ns} ns")
        if self.estimated_clock_ns is not None:
            lines.append(f"Estimated clock period: {self.estimated_clock_ns} ns")
        if self.latency_cycles is not None:
            lines.append(f"Latency: {self.latency_cycles} cycles ({self.latency_ns} ns)")
        if self.utilization_pct:
            util = ", ".join(f"{k}={v}%" for k, v in self.utilization_pct.items())
            lines.append(f"Resource utilization: {util}")
        if self.resources.get("Total"):
            totals = ", ".join(f"{k}={v}" for k, v in self.resources["Total"].items())
            lines.append(f"Total resources used: {totals}")
        if self.loop_notes:
            lines.append("Notes: " + " ".join(self.loop_notes))
        return "\n".join(lines)


def load_report(path: pathlib.Path) -> SynthesisReport:
    text = path.read_text(encoding="utf-8")

    top_match = re.search(r"Report for '([^']+)'", text)
    top_function = top_match.group(1) if top_match else path.stem

    clock_match = re.search(
        r"\|ap_clk\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|", text
    )
    target_clock = float(clock_match.group(1)) if clock_match else None
    estimated_clock = float(clock_match.group(2)) if clock_match else None

    latency_match = re.search(
        r"\|\s*min\s*\|\s*(\d+)\s*\|\s*max\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|", text
    )
    if latency_match:
        lo, hi, ns = latency_match.groups()
        latency_cycles = lo if lo == hi else f"{lo}-{hi}"
        latency_ns = float(ns)
    else:
        latency_cycles, latency_ns = None, None

    # Utilization table: rows of "|Name| BRAM | DSP | FF | LUT | URAM|"
    resources: dict[str, dict[str, str]] = {}
    util_pct: dict[str, str] = {}
    table_match = re.search(
        r"\|\s*Name\s*\|(.+?)\n(\+[-+]+\+\n)((?:\|.+\n)+)", text, re.DOTALL
    )
    if table_match:
        header_line = table_match.group(1)
        columns = [c.strip() for c in header_line.split("|") if c.strip()]
        row_block = table_match.group(3)
        for row in row_block.strip().splitlines():
            if set(row.strip()) <= {"+", "-"}:
                continue
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            name, values = cells[0], cells[1:]
            row_data = dict(zip(columns, values))
            if name == "Utilization (%)":
                util_pct = row_data
            else:
                resources[name] = row_data

    loop_notes = re.findall(r"^The .+?directive.+?\.$", text, re.MULTILINE | re.DOTALL)

    return SynthesisReport(
        top_function=top_function,
        target_clock_ns=target_clock,
        estimated_clock_ns=estimated_clock,
        latency_cycles=latency_cycles,
        latency_ns=latency_ns,
        resources=resources,
        utilization_pct=util_pct,
        loop_notes=[n.strip() for n in loop_notes],
        raw_text=text,
    )


def find_report(name: str, reports_dir: pathlib.Path) -> pathlib.Path | None:
    """Locate the report a user is asking about.

    Users often name a *loop* or a *variable* (e.g. 'fir_loop') rather than the
    top-level function the report is filed under ('fir_filter'). So:
      1. exact match on '<name>_report.txt'
      2. otherwise, the report whose text mentions the name
    Returns None if nothing matches or the match is ambiguous.
    """
    key = name.strip().lower().removesuffix("_report")
    exact = reports_dir / f"{key}_report.txt"
    if exact.exists():
        return exact

    matches = [
        path
        for path in sorted(reports_dir.glob("*_report.txt"))
        if key and key in path.read_text(encoding="utf-8").lower()
    ]
    return matches[0] if len(matches) == 1 else None
