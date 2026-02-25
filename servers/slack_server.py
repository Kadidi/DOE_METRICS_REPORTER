"""MCP server for querying Slack channels (Phase 1 MVP)."""

import json
import logging
import os
from datetime import datetime, timedelta
from fastmcp import Server

logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("slack_server")


def _get_slack_token() -> str:
    """Get Slack bot token from environment."""
    return os.getenv("SLACK_BOT_TOKEN", "")


@server.list_tools()
def list_tools() -> list:
    """List available Slack tools."""
    return [
        {
            "name": "list_channels",
            "description": "List available Slack channels",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "include_archived": {
                        "type": "boolean",
                        "description": "Include archived channels (default: false)",
                    },
                },
                "required": [],
            },
        },
        {
            "name": "query_channel_messages",
            "description": "Search messages in a Slack channel",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel name or ID",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search for (comma-separated)",
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Search last N days (default: 7)",
                    },
                },
                "required": ["channel", "keywords"],
            },
        },
        {
            "name": "get_message_thread",
            "description": "Get full thread context for a Slack message",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel name or ID",
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "Thread timestamp (parent message ts)",
                    },
                },
                "required": ["channel", "thread_ts"],
            },
        },
        {
            "name": "search_mentions",
            "description": "Find mentions of specific user or bot",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_or_bot": {
                        "type": "string",
                        "description": "Username or bot name to search for mentions",
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Search last N days (default: 7)",
                    },
                },
                "required": ["user_or_bot"],
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute a Slack tool."""
    try:
        if name == "list_channels":
            include_archived = arguments.get("include_archived", False)
            return await list_channels(include_archived)
        elif name == "query_channel_messages":
            channel = arguments["channel"]
            keywords = arguments["keywords"]
            days_back = arguments.get("days_back", 7)
            return await query_channel_messages(channel, keywords, days_back)
        elif name == "get_message_thread":
            channel = arguments["channel"]
            thread_ts = arguments["thread_ts"]
            return await get_message_thread(channel, thread_ts)
        elif name == "search_mentions":
            user_or_bot = arguments["user_or_bot"]
            days_back = arguments.get("days_back", 7)
            return await search_mentions(user_or_bot, days_back)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return json.dumps({"error": str(e)})


async def list_channels(include_archived: bool = False) -> str:
    """List available Slack channels.

    Args:
        include_archived: Whether to include archived channels

    Returns:
        JSON with channel list
    """
    # Placeholder implementation
    # In production: Use slack_sdk.WebClient
    result = {
        "channels": [
            {
                "id": "C12345",
                "name": "incidents",
                "topic": "System incidents and outages",
                "created": "2024-01-01",
                "members": 45,
            },
            {
                "id": "C12346",
                "name": "maintenance",
                "topic": "Scheduled maintenance windows",
                "created": "2024-01-01",
                "members": 30,
            },
            {
                "id": "C12347",
                "name": "ops-alerts",
                "topic": "Automated ops alerts",
                "created": "2024-06-01",
                "members": 20,
            },
        ],
        "total": 3,
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


async def query_channel_messages(channel: str, keywords: str, days_back: int = 7) -> str:
    """Search for messages in a channel.

    Args:
        channel: Channel name or ID
        keywords: Comma-separated keywords
        days_back: Number of days to search back

    Returns:
        JSON with matching messages
    """
    # Placeholder implementation
    keyword_list = [k.strip() for k in keywords.split(",")]
    result = {
        "channel": channel,
        "keywords": keyword_list,
        "days_back": days_back,
        "messages": [
            {
                "ts": "1737898200.000100",
                "user": "incident-bot",
                "text": "🚨 INCIDENT: Perlmutter nodes going down",
                "timestamp": "2025-01-26T14:30:00Z",
                "thread_ts": None,
                "reactions": ["🔴"],
                "reply_count": 12,
            },
            {
                "ts": "1737898500.000200",
                "user": "admin-user",
                "text": "We're investigating the perlmutter outage",
                "timestamp": "2025-01-26T14:35:00Z",
                "thread_ts": "1737898200.000100",
                "reactions": ["👍"],
                "reply_count": 0,
            },
        ],
        "total": 2,
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


async def get_message_thread(channel: str, thread_ts: str) -> str:
    """Get full thread for a message.

    Args:
        channel: Channel name or ID
        thread_ts: Thread timestamp (parent message ts)

    Returns:
        JSON with thread messages
    """
    # Placeholder implementation
    result = {
        "channel": channel,
        "thread_ts": thread_ts,
        "messages": [
            {
                "ts": thread_ts,
                "user": "incident-bot",
                "text": "🚨 INCIDENT: Perlmutter nodes down - status: investigating",
                "timestamp": "2025-01-26T14:30:00Z",
                "reactions": ["🔴"],
            },
            {
                "ts": "1737898300.000150",
                "user": "admin-user",
                "text": "@incident-bot Can you provide more details?",
                "timestamp": "2025-01-26T14:31:30Z",
                "reactions": [],
            },
            {
                "ts": "1737898400.000200",
                "user": "incident-bot",
                "text": "Investigating GPU issue on nodes 001-064",
                "timestamp": "2025-01-26T14:33:00Z",
                "reactions": [],
            },
        ],
        "reply_count": 3,
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


async def search_mentions(user_or_bot: str, days_back: int = 7) -> str:
    """Find mentions of a user or bot.

    Args:
        user_or_bot: Username or bot name
        days_back: Number of days to search back

    Returns:
        JSON with messages mentioning the user/bot
    """
    # Placeholder implementation
    result = {
        "user_or_bot": user_or_bot,
        "days_back": days_back,
        "mentions": [
            {
                "channel": "incidents",
                "ts": "1737898200.000100",
                "user": "admin-user",
                "text": f"@{user_or_bot} Check the perlmutter status",
                "timestamp": "2025-01-26T14:30:00Z",
            },
            {
                "channel": "ops-alerts",
                "ts": "1737884800.000050",
                "user": "monitoring-bot",
                "text": f"@{user_or_bot} High CPU usage detected",
                "timestamp": "2025-01-26T10:30:00Z",
            },
        ],
        "total": 2,
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


if __name__ == "__main__":
    # For testing the server standalone
    import asyncio

    async def test():
        """Test the server with sample tool calls."""
        result1 = await call_tool("list_channels", {})
        print("list_channels:", result1)

        result2 = await call_tool(
            "query_channel_messages",
            {"channel": "incidents", "keywords": "perlmutter,outage"},
        )
        print("query_channel_messages:", result2)

        result3 = await call_tool(
            "get_message_thread",
            {"channel": "incidents", "thread_ts": "1737898200.000100"},
        )
        print("get_message_thread:", result3)

    asyncio.run(test())
