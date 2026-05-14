#!/usr/bin/env python3
"""
Optional MBTA MCP server (Model Context Protocol) exposing MBTA V3 API as tools.

Install: pip install mcp httpx

Run: python mbta_mcp_server.py
"""

from __future__ import annotations

import json

import httpx

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:  # pragma: no cover
    raise SystemExit("Install dependencies: pip install mcp httpx") from e

MBTA_BASE = "https://api-v3.mbta.com"

mcp = FastMCP("mbta-transit")


async def _get(path: str, params: dict | None = None) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(f"{MBTA_BASE}{path}", params=params or {})
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)[:200_000]


@mcp.tool()
async def get_vehicles(route_type: str = "3") -> str:
    """Real-time vehicle positions. route_type: 0,1 = subway, 3 = bus."""
    return await _get("/vehicles", {"filter[route_type]": route_type, "page[limit]": "200"})


@mcp.tool()
async def get_predictions(stop_id: str) -> str:
    """Predictions for a stop id (e.g. place-sstat)."""
    return await _get("/predictions", {"filter[stop]": stop_id, "page[limit]": "100"})


@mcp.tool()
async def get_alerts(route_id: str | None = None) -> str:
    """Active alerts, optionally filtered by route id."""
    params: dict[str, str] = {"page[limit]": "100"}
    if route_id:
        params["filter[route]"] = route_id
    return await _get("/alerts", params)


@mcp.tool()
async def get_schedules(route_id: str, service_date: str) -> str:
    """Schedules for a route on YYYY-MM-DD (America/New_York service date)."""
    return await _get(
        "/schedules",
        {"filter[route]": route_id, "filter[date]": service_date, "page[limit]": "200"},
    )


@mcp.tool()
async def get_route_info(route_id: str) -> str:
    """Single route resource."""
    return await _get(f"/routes/{route_id}")


if __name__ == "__main__":
    mcp.run()
