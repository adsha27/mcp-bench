import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    tool: str
    success: bool
    latency_ms: float
    error: str | None = None
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    def __init__(self):
        self._results: list[ToolResult] = []

    def record(self, result: ToolResult):
        self._results.append(result)

    def summary(self) -> dict[str, dict]:
        by_tool: dict[str, list[ToolResult]] = defaultdict(list)
        for r in self._results:
            by_tool[r.tool].append(r)

        out = {}
        for tool, results in by_tool.items():
            latencies = [r.latency_ms for r in results]
            successes = sum(1 for r in results if r.success)
            errors = defaultdict(int)
            for r in results:
                if r.error:
                    errors[r.error] += 1

            out[tool] = {
                "calls": len(results),
                "success": successes,
                "fail": len(results) - successes,
                "success_rate": round(successes / len(results) * 100, 1),
                "p50_ms": round(statistics.median(latencies), 1),
                "p95_ms": round(_percentile(latencies, 95), 1),
                "p99_ms": round(_percentile(latencies, 99), 1),
                "errors": dict(errors),
            }
        return out

    def all_results(self) -> list[ToolResult]:
        return list(self._results)


def _percentile(data: list[float], p: int) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]
