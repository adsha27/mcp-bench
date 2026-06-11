#!/usr/bin/env python3
"""
Minimal MCP server for benchmarking — no real tools, just latency simulation.
Run: python examples/mock_server.py [--slow]

Tools exposed:
  echo        — returns input immediately
  slow_echo   — simulates a 500ms external call
  flaky_tool  — fails 30% of the time (simulates real-world failure rates)
"""

import asyncio
import json
import random
import sys

TOOLS = [
    {
        "name": "echo",
        "description": "Returns the input string immediately",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
    {
        "name": "slow_echo",
        "description": "Simulates a 500ms external API call then returns input",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
    {
        "name": "flaky_tool",
        "description": "Fails 30% of the time — baseline for error-rate benchmarks",
        "inputSchema": {
            "type": "object",
            "properties": {"payload": {"type": "string"}},
            "required": ["payload"],
        },
    },
]

_id = 0


def _reply(id, result):
    return json.dumps({"jsonrpc": "2.0", "id": id, "result": result})


def _error(id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})


async def handle(line: str) -> str | None:
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return None

    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return _reply(msg_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mock-mcp-server", "version": "0.1.0"},
        })

    if method == "tools/list":
        return _reply(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "echo":
            return _reply(msg_id, {"content": [{"type": "text", "text": args.get("message", "")}]})

        if name == "slow_echo":
            await asyncio.sleep(0.5)
            return _reply(msg_id, {"content": [{"type": "text", "text": args.get("message", "")}]})

        if name == "flaky_tool":
            if random.random() < 0.3:
                return _error(msg_id, -32000, "flaky_tool: simulated failure")
            return _reply(msg_id, {"content": [{"type": "text", "text": args.get("payload", "")}]})

        return _error(msg_id, -32601, f"Unknown tool: {name}")

    return None


async def main():
    reader = asyncio.StreamReader()
    proto = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: proto, sys.stdin)

    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        lambda: asyncio.BaseProtocol(), sys.stdout.buffer
    )

    import io
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

    async for line in reader:
        response = await handle(line.decode().strip())
        if response:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
