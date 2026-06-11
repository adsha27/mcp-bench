import pytest
from mcp_bench.metrics import MetricsCollector, ToolResult


def test_success_rate():
    c = MetricsCollector()
    c.record(ToolResult(tool="echo", success=True, latency_ms=10.0))
    c.record(ToolResult(tool="echo", success=True, latency_ms=20.0))
    c.record(ToolResult(tool="echo", success=False, latency_ms=5.0, error="timeout"))
    s = c.summary()["echo"]
    assert s["calls"] == 3
    assert abs(s["success_rate"] - 66.7) < 0.2
    assert s["fail"] == 1


def test_percentiles():
    c = MetricsCollector()
    for ms in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        c.record(ToolResult(tool="t", success=True, latency_ms=float(ms)))
    s = c.summary()["t"]
    assert s["p50_ms"] == 55.0
    assert s["p95_ms"] == 95.0
