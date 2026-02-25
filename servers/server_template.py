"""Template for creating new MCP servers for DOE_METRICS_REPORTER.

Copy this file and follow the pattern below to add new API integrations.
"""

import logging
from fastmcp import Server
import os

logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("template_server")


@server.list_tools()
def list_tools() -> list:
    """List available tools provided by this server."""
    return [
        {
            "name": "template_tool",
            "description": "A template tool that demonstrates the structure",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to execute",
                    },
                },
                "required": ["query"],
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with given arguments.

    Args:
        name: Tool name to execute
        arguments: Tool arguments dict

    Returns:
        JSON string with results
    """
    try:
        if name == "template_tool":
            return await template_tool(arguments["query"])
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return f"Error: {str(e)}"


async def template_tool(query: str) -> str:
    """Example tool implementation.

    Args:
        query: Query string

    Returns:
        Result as JSON string
    """
    import json

    # Implementation steps:
    # 1. Validate input
    # 2. Check cache (optional, use CacheManager if needed)
    # 3. Call external API/service
    # 4. Transform response to data model
    # 5. Cache result (optional)
    # 6. Return as JSON

    result = {
        "query": query,
        "results": [],
        "count": 0,
        "cached_at": None,
        "cache_hit": False,
    }

    return json.dumps(result)


if __name__ == "__main__":
    # For testing the server standalone
    import asyncio

    async def test():
        """Test the server with sample tool call."""
        result = await call_tool("template_tool", {"query": "test"})
        print(result)

    asyncio.run(test())
