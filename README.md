# mcp-bench

Load testing and benchmarking for MCP (Model Context Protocol) tool servers.

Built out of a real production problem: we were running a government-services WhatsApp chatbot with a large MCP tool layer. The observability setup showed some tools failing silently — `check_application_status` had a 0% success rate over 22 live calls, and nobody caught it until a user got stuck in a loop. Unit tests passed. The tool worked in isolation. It fell apart under real usage patterns.

mcp-bench is what we built to catch that class of problem: load test the actual tool server under realistic concurrency, see which tools degrade, before users find out.

## What it measures

- Per-tool latency: p50 / p95 / p99
- Success rate and failure breakdown by error type
- Throughput under configurable concurrency

## Usage

```bash
git clone https://github.com/adsha27/mcp-bench
cd mcp-bench && pip install -e .

# Run against an stdio MCP server
mcp-bench run --server "python myserver.py" --users 100 --concurrency 10

# HTTP transport
mcp-bench run --http http://localhost:3000 --users 100 --concurrency 20

# Write an HTML report
mcp-bench run --server "python myserver.py" --users 100 --report report.html
```

## Sample output

Running against the included mock server (100 users, 10 concurrency):

```
Benchmark results (300 total calls, 8.2s)

tool                           calls  success    fail   p50ms   p95ms   p99ms
echo                             100    100.0%       0       1       3       5
slow_echo                        100    100.0%       0     503     512     521
flaky_tool                       100     69.3%      31      <1       2       4  <-- failing
```

`flaky_tool` is configured to fail 30% of the time. In production, this is the pattern that surfaces tools with rate limits, flaky upstream APIs, or connection pool exhaustion under concurrency.

## Mock server

`examples/mock_server.py` ships with three tools for testing without a real MCP server:

| Tool | Behavior |
|------|----------|
| `echo` | Returns immediately |
| `slow_echo` | 500ms delay (simulates an external API call) |
| `flaky_tool` | Fails 30% of the time |

## Structure

```
mcp_bench/
  runner.py     async load runner with asyncio.Semaphore
  client.py     MCP client — stdio and HTTP transports
  metrics.py    p50/p95/p99 tracking, per-tool aggregation
  report.py     HTML report generator
examples/
  mock_server.py
tests/
```

## Install

```bash
pip install -e .
# or
pip install mcp-bench  # once published
```
