"""MCP server for querying NERSC SFAPI status and outages."""

import json
import logging

from fastmcp import FastMCP

from query_sfapi import (
    HAS_SFAPI,
    get_all_outages,
    get_all_systems_status,
    get_last_swo,
    get_planned_outages,
    get_recent_outages,
    get_system_status,
    get_system_wide_outages,
    get_unplanned_outages,
    query_sfapi,
)

logger = logging.getLogger(__name__)

server = FastMCP("sfapi_server")


def _json_result(result) -> str:
    """Serialize a Python result to JSON."""
    return json.dumps(result)


async def call_tool(name: str, arguments: dict) -> str:
    """Compatibility wrapper for direct module testing."""
    try:
        if name == "query_sfapi":
            return await sfapi_query(arguments["question"])
        if name == "get_all_systems_status":
            return await sfapi_all_systems_status()
        if name == "get_system_status":
            return await sfapi_system_status(arguments.get("system", "perlmutter"))
        if name == "get_all_outages":
            return await sfapi_all_outages()
        if name == "get_planned_outages":
            return await sfapi_planned_outages()
        if name == "get_unplanned_outages":
            return await sfapi_unplanned_outages()
        if name == "get_recent_outages":
            return await sfapi_recent_outages(arguments.get("days", 7))
        if name == "get_system_wide_outages":
            return await sfapi_system_wide(arguments.get("limit", 10))
        if name == "get_last_swo":
            return await sfapi_last_swo()
        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        logger.error("Error in %s: %s", name, e)
        return json.dumps({"error": str(e)})


@server.tool(name="query_sfapi", description="Run a natural-language query against SFAPI status/outage data.")
async def sfapi_query(question: str) -> str:
    """Run a natural-language SFAPI query."""
    return _json_result(query_sfapi(question))


@server.tool(name="get_all_systems_status", description="Get public status for all NERSC systems.")
async def sfapi_all_systems_status() -> str:
    """Get public status for all systems."""
    return _json_result(get_all_systems_status())


@server.tool(
    name="get_system_status",
    description="Get authenticated status for a specific NERSC system, such as perlmutter.",
)
async def sfapi_system_status(system: str = "perlmutter") -> str:
    """Get authenticated status for a specific system."""
    result = {
        "authenticated": HAS_SFAPI,
        "system": system,
        "data": get_system_status(system),
    }
    return _json_result(result)


@server.tool(name="get_all_outages", description="Get all SFAPI outages across NERSC systems.")
async def sfapi_all_outages() -> str:
    """Get all outages."""
    return _json_result(get_all_outages())


@server.tool(name="get_planned_outages", description="Get planned or scheduled outages.")
async def sfapi_planned_outages() -> str:
    """Get planned outages."""
    return _json_result(get_planned_outages())


@server.tool(name="get_unplanned_outages", description="Get currently active unplanned outages.")
async def sfapi_unplanned_outages() -> str:
    """Get unplanned outages."""
    return _json_result(get_unplanned_outages())


@server.tool(name="get_recent_outages", description="Get outages from the last N days.")
async def sfapi_recent_outages(days: int = 7) -> str:
    """Get recent outages."""
    return _json_result(get_recent_outages(days=days))


@server.tool(name="get_system_wide_outages", description="Get recent system-wide outages (SWOs).")
async def sfapi_system_wide(limit: int = 10) -> str:
    """Get system-wide outages."""
    return _json_result(get_system_wide_outages(limit=limit))


@server.tool(name="get_last_swo", description="Get the most recent system-wide outage.")
async def sfapi_last_swo() -> str:
    """Get the most recent system-wide outage."""
    return _json_result(get_last_swo())


if __name__ == "__main__":
    import asyncio

    async def test():
        """Test the server with sample tool calls."""
        print(await call_tool("get_all_systems_status", {}))
        print(await call_tool("query_sfapi", {"question": "What maintenance is planned?"}))

    asyncio.run(test())
