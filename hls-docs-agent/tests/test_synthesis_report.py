import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.synthesis_report import load_report

REPORT_PATH = pathlib.Path(__file__).resolve().parent.parent / "sample_reports" / "fir_filter_report.txt"


def test_load_report_extracts_top_function():
    report = load_report(REPORT_PATH)
    assert report.top_function == "fir_filter"


def test_load_report_extracts_timing():
    report = load_report(REPORT_PATH)
    assert report.target_clock_ns == 10.0
    assert report.estimated_clock_ns == 8.34


def test_load_report_extracts_latency():
    report = load_report(REPORT_PATH)
    assert report.latency_cycles == "81"
    assert report.latency_ns == 675.54


def test_load_report_extracts_utilization():
    report = load_report(REPORT_PATH)
    assert report.resources["Total"]["DSP"] == "3"
    assert report.utilization_pct["LUT"] == "0"


def test_as_context_string_includes_key_facts():
    report = load_report(REPORT_PATH)
    ctx = report.as_context_string()
    assert "fir_filter" in ctx
    assert "675.54" in ctx
    assert "DSP=3" in ctx
