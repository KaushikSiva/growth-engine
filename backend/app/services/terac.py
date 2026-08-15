from __future__ import annotations
import json
from typing import Any
from uuid import uuid4
import httpx
from ..config import get_settings


class TeracMCP:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.terac_api_key:
            raise RuntimeError("TERAC_API_KEY is not configured. No Terac opportunity was created.")
        self.session_id: str | None = None
        self.request_id = 0

    def _next(self) -> int:
        self.request_id += 1
        return self.request_id

    @staticmethod
    def _decode(response: httpx.Response) -> dict:
        if "text/event-stream" in response.headers.get("content-type", ""):
            events = []
            for line in response.text.splitlines():
                if line.startswith("data:"):
                    try: events.append(json.loads(line[5:].strip()))
                    except json.JSONDecodeError: continue
            if not events:
                raise RuntimeError("Terac MCP returned an empty event stream.")
            return events[-1]
        return response.json()

    async def _post(self, client: httpx.AsyncClient, method: str, params: dict | None = None, notification: bool = False) -> dict:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not notification: payload["id"] = self._next()
        if params is not None: payload["params"] = params
        headers = {"x-api-key": self.settings.terac_api_key, "Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        if self.session_id: headers["Mcp-Session-Id"] = self.session_id
        response = await client.post(self.settings.terac_mcp_url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"Terac MCP unavailable ({response.status_code}): {response.text[:500]}")
        self.session_id = response.headers.get("Mcp-Session-Id", self.session_id)
        body = self._decode(response) if response.content else {}
        if body.get("error"):
            raise RuntimeError(f"Terac MCP error: {body['error'].get('message', body['error'])}")
        return body.get("result", body)

    async def _ready(self, client: httpx.AsyncClient) -> None:
        await self._post(client, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "reproclip-company", "version": "0.1.0"}})
        await self._post(client, "notifications/initialized", notification=True)

    async def call(self, tool: str, arguments: dict) -> dict:
        async with httpx.AsyncClient(timeout=90) as client:
            await self._ready(client)
            listed = await self._post(client, "tools/list", {})
            names = {item.get("name") for item in listed.get("tools", [])}
            if tool not in names:
                raise RuntimeError(f"Terac MCP does not currently expose {tool}. Available tools: {', '.join(sorted(str(name) for name in names if name))}")
            result = await self._post(client, "tools/call", {"name": tool, "arguments": arguments})
            if result.get("isError"):
                raise RuntimeError(f"Terac {tool} failed: {result.get('content')}")
            structured = result.get("structuredContent")
            if isinstance(structured, dict): return structured
            texts = [item.get("text", "") for item in result.get("content", []) if item.get("type") == "text"]
            for text in texts:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict): return parsed
                except json.JSONDecodeError:
                    pass
            return {"content": texts}

    async def request_feasibility(self, role: str, task: str, count: int) -> dict:
        return await self.call("terac_request_feasibility", {"role": role, "task": task, "count": count})

    async def launch_priced_request(self, request_id: str) -> dict:
        return await self.call("terac_launch_draft_opportunity", {"request_id": request_id})

    async def submissions(self, opportunity_id: str | None = None) -> dict:
        arguments = {"opportunity_id": opportunity_id} if opportunity_id else {}
        return await self.call("terac_get_submissions", arguments)


def creator_brief(campaign: dict) -> dict:
    return {
        "product": "ReproClip",
        "target": campaign["audience"],
        "goal": "Get people interested in trying or voluntarily supporting the open-source ReproClip project.",
        "content": "15–30 second original short-form promotional video",
        "recommended_format": "Show an ugly/raw screen recording first, then the polished ReproClip result.",
        "core_message": campaign["hook"],
        "cta": "Try ReproClip. If it saves you time, support the open-source project for $5.",
        "requirements": ["Original content", "No copyrighted music/assets", "No false claims", "Clear ReproClip demonstration", "Submit final video", "Submit a social URL only when the task and platform rules explicitly permit publishing"],
    }


def creative_test_brief(campaign: dict, creatives: list[dict]) -> dict:
    return {
        "audience": "General population, with no specialist knowledge required",
        "goal": "Measure which real creative communicates ReproClip most clearly and creates the most honest intent.",
        "creatives": creatives,
        "questions": [
            "Which one makes you most interested in trying ReproClip?",
            "Which one explains the product most clearly?",
            "Which one feels most trustworthy?",
            "Which would you be most likely to click?",
            "In one sentence, what do you think ReproClip does?",
        ],
        "output": "Per-creative clarity, click intent, support intent, preference share, response count, and raw responses.",
    }
