"""Generate an HTML benchmark report from collected metrics."""

import json
from datetime import datetime

from mcp_bench.metrics import MetricsCollector


def generate_html(collector: MetricsCollector, output_path: str, title: str = "MCP Benchmark"):
    summary = collector.summary()
    results_json = json.dumps([
        {
            "tool": r.tool,
            "success": r.success,
            "latency_ms": round(r.latency_ms, 2),
            "error": r.error,
            "timestamp": r.timestamp,
        }
        for r in collector.all_results()
    ])

    rows = ""
    for tool, s in sorted(summary.items()):
        flag = ' style="color:red;font-weight:bold"' if s["success_rate"] < 80 else ""
        rows += f"""
        <tr>
            <td{flag}>{tool}</td>
            <td>{s['calls']}</td>
            <td{flag}>{s['success_rate']}%</td>
            <td>{s['fail']}</td>
            <td>{s['p50_ms']}</td>
            <td>{s['p95_ms']}</td>
            <td>{s['p99_ms']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><title>{title}</title>
<style>
body {{ font-family: monospace; max-width: 900px; margin: 40px auto; color: #111; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; border-bottom: 2px solid #333; padding: 6px 12px; }}
td {{ padding: 4px 12px; border-bottom: 1px solid #eee; }}
h1 {{ font-size: 18px; }}
.meta {{ color: #666; font-size: 13px; margin-bottom: 24px; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | {sum(s['calls'] for s in summary.values())} total calls</div>
<table>
<tr><th>Tool</th><th>Calls</th><th>Success</th><th>Fail</th><th>p50ms</th><th>p95ms</th><th>p99ms</th></tr>
{rows}
</table>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Report written to {output_path}")
