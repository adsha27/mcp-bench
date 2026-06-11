"""
Async load runner for MCP tool benchmarks.
Simulates N users calling tools with configurable concurrency.
"""

import asyncio
import time
from collections.abc import Callable

from mcp_bench.metrics import MetricsCollector, ToolResult


async def run_benchmark(
    tool_fn: Callable[[str], any],
    tools: list[str],
    users: int = 100,
    concurrency: int = 10,
    calls_per_user: int = 1,
) -> MetricsCollector:
    """
    Run a load benchmark against a set of tools.

    Args:
        tool_fn: async callable(tool_name) -> result. Should raise on failure.
        tools: list of tool names to benchmark
        users: total number of simulated users
        concurrency: max parallel calls
        calls_per_user: how many tool calls each user makes
    """
    collector = MetricsCollector()
    semaphore = asyncio.Semaphore(concurrency)

    async def single_call(tool: str):
        async with semaphore:
            start = time.perf_counter()
            try:
                await tool_fn(tool)
                latency_ms = (time.perf_counter() - start) * 1000
                collector.record(ToolResult(tool=tool, success=True, latency_ms=latency_ms))
            except Exception as e:
                latency_ms = (time.perf_counter() - start) * 1000
                collector.record(ToolResult(
                    tool=tool, success=False, latency_ms=latency_ms,
                    error=type(e).__name__
                ))

    tasks = []
    for _ in range(users):
        for tool in tools:
            for _ in range(calls_per_user):
                tasks.append(single_call(tool))

    await asyncio.gather(*tasks)
    return collector


def print_summary(collector: MetricsCollector, duration_s: float):
    summary = collector.summary()
    total = sum(v["calls"] for v in summary.values())
    print(f"\nBenchmark results ({total} total calls, {duration_s:.1f}s)")
    print(f"\n{'tool':<30} {'calls':>6} {'success':>8} {'fail':>6} {'p50ms':>7} {'p95ms':>7} {'p99ms':>7}")
    print("-" * 80)
    for tool, s in sorted(summary.items()):
        flag = "  <-- failing" if s["success_rate"] < 80 else ""
        print(
            f"{tool:<30} {s['calls']:>6} {s['success_rate']:>7.1f}% {s['fail']:>6} "
            f"{s['p50_ms']:>7.0f} {s['p95_ms']:>7.0f} {s['p99_ms']:>7.0f}{flag}"
        )
