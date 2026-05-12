"""MCP server for Perlmutter utilization reports."""

import json
import logging

from fastmcp import FastMCP

from utilization_backend import UtilizationReportError, UtilizationRequest, run_utilization_report

logger = logging.getLogger(__name__)

server = FastMCP("utilization_server")


async def call_tool(name: str, arguments: dict) -> str:
    """Compatibility wrapper for direct module testing."""
    try:
        if name == "report_utilization":
            return await report_utilization(
                mode=arguments["mode"],
                date=arguments["date"],
                resource=arguments.get("resource", "gpu"),
                summary=arguments.get("summary", False),
                exclude_below=arguments.get("exclude_below"),
                index=arguments.get("index"),
            )
        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        logger.error("Error in %s: %s", name, e)
        return json.dumps({"error": str(e)})


@server.tool(
    name="report_utilization",
    description="Generate a daily or monthly Perlmutter CPU/GPU utilization report.",
)
async def report_utilization(
    mode: str,
    date: str,
    resource: str = "gpu",
    include_root: bool = True,
    cap_only: bool = False,
    compare_with_gabor: bool = False,
) -> str:
    """Generate a utilization report using native IRIS Elasticsearch SQL logic."""
    try:
        result = run_utilization_report(
            UtilizationRequest(
                mode=mode,
                date=date,
                resource=resource,
                include_root=include_root,
                cap_only=cap_only,
                compare_with_gabor=compare_with_gabor,
            )
        )
    except UtilizationReportError as e:
        return json.dumps({"error": str(e)})
    return json.dumps(result)


if __name__ == "__main__":
    import asyncio

    async def test():
        """Exercise the utilization tool."""
        print(
            await call_tool(
                "report_utilization",
                {"mode": "day", "date": "2026-01-01", "resource": "gpu"},
            )
        )

    asyncio.run(test())
