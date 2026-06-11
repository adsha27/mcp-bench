# mcp-bench

Benchmark harness for MCP (Model Context Protocol) tool servers. Measures latency, success rate, and throughput under load.

Built from production experience running 46 MCP tools in a live government-services chatbot. When tools fail silently, users get stuck. This catches that before it ships.

## What it does

- Load test any MCP server with configurable concurrency and user count
- Measure per-tool latency (p50, p95, p99) and success/failure rates
- Generate a report showing which tools are slow or flaky under load
- Works with any MCP server that speaks the stdio or HTTP transport

## Usage

```bash
pip install mcp-bench

# Run against an MCP server
mcp-bench run --server "python myserver.py" --tools search_tool,submit_tool --users 100 --concurrency 10

# Or point at an HTTP MCP endpoint
mcp-bench run --server "http://localhost:3000/mcp" --users 100

# Generate HTML report
mcp-bench report results.json --output report.html
```

## Example output

```
Tool benchmark results (100 users, 10 concurrent)
Duration: 12.4s

tool                     calls  success  fail   p50ms  p95ms  p99ms
search_opportunities       100    94%     6%      340    890   1420
submit_application         100    98%     2%      210    450    890
get_profile                100   100%     0%       80    140    200
check_status               100    72%    28%     1200   3400   5000  <-- failing

check_status is failing at 28% - likely a timeout or upstream API issue.
```

## Report

`mcp-bench report` produces an HTML file with:
- Per-tool success rate over time (useful for spotting degradation mid-run)
- Latency histogram per tool
- Error breakdown by error type (timeout, connection, tool error)
- Comparison across multiple benchmark runs

## Why this exists

Production MCP deployments fail in ways that unit tests miss. A tool that works fine under 1 user can fail under 10 if it hits a rate limit, a shared connection pool, or a flaky upstream API. The only way to know is to run it under load and watch the numbers.

## Structure

```
mcp_bench/
  runner.py      Async load runner
  client.py      MCP client (stdio + HTTP)
  report.py      HTML report generator
  metrics.py     Latency and rate tracking
examples/
  mock_server.py Example MCP server for testing
tests/
```

## Install

```bash
pip install mcp-bench
# or
git clone https://github.com/adsha27/mcp-bench
cd mcp-bench
pip install -e .
```
