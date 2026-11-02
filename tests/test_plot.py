"""Tests for bench/plot.py (loaded by path; bench/ is not a package)."""

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PLOT = Path(__file__).resolve().parents[1] / "bench" / "plot.py"
spec = importlib.util.spec_from_file_location("bench_plot", PLOT)
plot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot)


def run_json(label, gemm, h2d):
    return {
        "label": label,
        "timestamp": "2026-11-02T00:00:00+00:00",
        "environment": {"device": "AMD Instinct MI210", "kernel": "6.8.0", "hip": "6.4"},
        "metrics": [
            {"key": "gemm_fp32", "name": "GEMM FP32", "unit": "TFLOPS", "value": gemm},
            {"key": "h2d", "name": "Host → device copy", "unit": "GB/s", "value": h2d},
        ],
    }


@pytest.fixture
def results(tmp_path):
    (tmp_path / "baremetal.json").write_text(json.dumps(run_json("baremetal", 40.0, 25.0)))
    (tmp_path / "guest.json").write_text(json.dumps(run_json("guest", 39.0, 26.0)))
    return tmp_path


def test_pair_metrics_ratio():
    rows = plot.pair_metrics(run_json("b", 40.0, 25.0), run_json("g", 30.0, 25.0))
    assert [round(r["pct"], 1) for r in rows] == [75.0, 100.0]


def test_pair_metrics_skips_missing_and_zero():
    bare = run_json("b", 0.0, 25.0)
    guest = run_json("g", 30.0, 25.0)
    guest["metrics"] = guest["metrics"][:1]  # guest lacks h2d
    assert plot.pair_metrics(bare, guest) == []


def test_writes_markdown_and_both_svgs(results, capsys):
    assert plot.main(["--results-dir", str(results)]) == 0
    md = (results / "comparison.md").read_text()
    assert "| GEMM FP32 | 40.0 TFLOPS | 39.0 TFLOPS | 97.5% |" in md
    assert "comparison-dark.svg" in md
    for theme in ("light", "dark"):
        svg = ET.parse(results / f"comparison-{theme}.svg").getroot()  # well-formed XML
        text = "".join(svg.itertext())
        assert "97.5%" in text and "104.0%" in text
        assert plot.THEMES[theme]["bar"] in (results / f"comparison-{theme}.svg").read_text()


def test_missing_input_exits_2(tmp_path, capsys):
    assert plot.main(["--results-dir", str(tmp_path)]) == 2
    assert "baremetal.json" in capsys.readouterr().err
