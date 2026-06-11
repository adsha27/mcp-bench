"""
Thin async MCP client for stdio and HTTP (SSE) transports.
Only implements tool listing and calling — enough for benchmarking.
"""

import asyncio
import json
import subprocess
from collections.abc import AsyncIterator


class StdioMCPClient:
    """
    Talks to an MCP server process over stdio.
    Sends JSON-RPC requests, reads JSON-RPC responses.
    """

    def __init__(self, command: list[str]):
        self.command = command
        self._proc: asyncio.subprocess.Process | None = None
        self._id = 0

    async def __aenter__(self):
        self._proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await self._initialize()
        return self

    async def __aexit__(self, *_):
        if self._proc:
            self._proc.terminate()
            await self._proc.wait()

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    async def _send(self, method: str, params: dict) -> dict:
        msg = json.dumps({"jsonrpc": "2.0", "id": self._next_id(), "method": method, "params": params})
        self._proc.stdin.write((msg + "\n").encode())
        await self._proc.stdin.drain()
        line = await self._proc.stdout.readline()
        return json.loads(line)

    async def _initialize(self):
        await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-bench", "version": "0.1.0"},
        })

    async def list_tools(self) -> list[dict]:
        resp = await self._send("tools/list", {})
        return resp.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> dict:
        resp = await self._send("tools/call", {"name": name, "arguments": arguments})
        return resp.get("result", {})


class HttpMCPClient:
    """
    Talks to an MCP server over HTTP+SSE (streamable transport).
    Requires httpx.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = None
        self._id = 0

    async def __aenter__(self):
        import httpx
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, *_):
        if self._client:
            await self._client.aclose()

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    async def _rpc(self, method: str, params: dict) -> dict:
        payload = {"jsonrpc": "2.0", "id": self._next_id(), "method": method, "params": params}
        resp = await self._client.post("/mcp", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def list_tools(self) -> list[dict]:
        resp = await self._rpc("tools/list", {})
        return resp.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> dict:
        resp = await self._rpc("tools/call", {"name": name, "arguments": arguments})
        return resp.get("result", {})
