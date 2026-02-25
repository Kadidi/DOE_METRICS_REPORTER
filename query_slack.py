#!/usr/bin/env python3
"""Real Slack integration for querying messages."""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    HAS_SLACK_SDK = True
except ImportError:
    HAS_SLACK_SDK = False

# Import central config
try:
    from config import get_slack_token
except ImportError:
    def get_slack_token():
        """Fallback if config.py not available."""
        return os.getenv("SLACK_BOT_TOKEN")


class SlackQuerier:
    """Query Slack channels and messages."""

    def __init__(self, token: Optional[str] = None):
        """Initialize Slack client.

        Args:
            token: Slack bot token (optional - uses central config if not provided)
        """
        if not HAS_SLACK_SDK:
            raise ImportError("slack_sdk not installed. Run: pip install slack-sdk")

        # Use provided token, or get from central config
        self.token = token or get_slack_token()
        if not self.token:
            raise ValueError(
                "Slack token not configured. "
                "Contact your administrator or set SLACK_BOT_TOKEN environment variable."
            )

        self.client = WebClient(token=self.token)

    def list_channels(self, include_archived: bool = False) -> List[Dict]:
        """List all accessible channels.

        Args:
            include_archived: Include archived channels

        Returns:
            List of channel dicts
        """
        try:
            response = self.client.conversations_list(
                exclude_archived=not include_archived,
                types="public_channel,private_channel"
            )

            channels = []
            for channel in response["channels"]:
                channels.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "topic": channel.get("topic", {}).get("value", ""),
                    "is_archived": channel.get("is_archived", False),
                    "num_members": channel.get("num_members", 0),
                })

            return channels

        except SlackApiError as e:
            print(f"Error listing channels: {e}")
            return []

    def search_messages(self, query: str, count: int = 20) -> List[Dict]:
        """Search all messages across channels.

        Args:
            query: Search query
            count: Max results to return

        Returns:
            List of message dicts
        """
        try:
            response = self.client.search_messages(
                query=query,
                count=count,
                sort="timestamp",
                sort_dir="desc"
            )

            messages = []
            for match in response.get("messages", {}).get("matches", []):
                messages.append({
                    "text": match.get("text", ""),
                    "user": match.get("username", "Unknown"),
                    "channel": match.get("channel", {}).get("name", "Unknown"),
                    "timestamp": match.get("ts", ""),
                    "permalink": match.get("permalink", ""),
                })

            return messages

        except SlackApiError as e:
            print(f"Error searching messages: {e}")
            return []

    def get_channel_messages(
        self,
        channel_name: str,
        days_back: int = 7,
        keywords: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get messages from a specific channel.

        Args:
            channel_name: Channel name (without #)
            days_back: Number of days to look back
            keywords: Optional keywords to filter messages

        Returns:
            List of message dicts
        """
        try:
            # Find channel ID
            channels = self.list_channels()
            channel_id = None
            for ch in channels:
                if ch["name"] == channel_name:
                    channel_id = ch["id"]
                    break

            if not channel_id:
                print(f"Channel '{channel_name}' not found")
                return []

            # Calculate oldest timestamp
            oldest = datetime.now() - timedelta(days=days_back)
            oldest_ts = oldest.timestamp()

            # Get messages
            response = self.client.conversations_history(
                channel=channel_id,
                oldest=str(oldest_ts)
            )

            messages = []
            for msg in response.get("messages", []):
                text = msg.get("text", "")

                # Filter by keywords if provided
                if keywords:
                    if not any(kw.lower() in text.lower() for kw in keywords):
                        continue

                messages.append({
                    "text": text,
                    "user": msg.get("user", "Unknown"),
                    "timestamp": msg.get("ts", ""),
                    "thread_ts": msg.get("thread_ts"),
                    "reactions": msg.get("reactions", []),
                })

            return messages

        except SlackApiError as e:
            print(f"Error getting channel messages: {e}")
            return []

    def get_thread(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """Get all messages in a thread.

        Args:
            channel_id: Channel ID
            thread_ts: Thread timestamp

        Returns:
            List of thread messages
        """
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )

            messages = []
            for msg in response.get("messages", []):
                messages.append({
                    "text": msg.get("text", ""),
                    "user": msg.get("user", "Unknown"),
                    "timestamp": msg.get("ts", ""),
                })

            return messages

        except SlackApiError as e:
            print(f"Error getting thread: {e}")
            return []


def search_slack_simple(query: str, max_results: int = 10) -> str:
    """Simple Slack search function for use in smart_ask.

    Args:
        query: Search query
        max_results: Maximum results

    Returns:
        Formatted string with results
    """
    if not HAS_SLACK_SDK:
        return "Slack SDK not installed. Run: pip install slack-sdk"

    if not os.getenv("SLACK_BOT_TOKEN"):
        return "SLACK_BOT_TOKEN not set. Cannot query Slack."

    try:
        querier = SlackQuerier()
        messages = querier.search_messages(query, count=max_results)

        if not messages:
            return f"No Slack messages found for: {query}"

        result = f"Found {len(messages)} Slack message(s):\n\n"
        for i, msg in enumerate(messages, 1):
            result += f"{i}. From #{msg['channel']} by {msg['user']}:\n"
            result += f"   {msg['text']}\n"
            if msg.get('permalink'):
                result += f"   Link: {msg['permalink']}\n"
            result += "\n"

        return result

    except Exception as e:
        return f"Error querying Slack: {e}"


if __name__ == "__main__":
    # Test Slack integration
    import sys

    if not HAS_SLACK_SDK:
        print("Error: slack-sdk not installed")
        print("Run: pip install slack-sdk")
        sys.exit(1)

    if not os.getenv("SLACK_BOT_TOKEN"):
        print("Error: SLACK_BOT_TOKEN not set")
        print("Set: export SLACK_BOT_TOKEN='xoxb-...'")
        sys.exit(1)

    querier = SlackQuerier()

    # List channels
    print("Channels:")
    print("=" * 80)
    channels = querier.list_channels()
    for ch in channels[:10]:  # Show first 10
        print(f"  #{ch['name']} - {ch['topic']}")
    print()

    # Search messages
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "incident"
    print(f"Searching for: {query}")
    print("=" * 80)
    messages = querier.search_messages(query, count=5)
    for msg in messages:
        print(f"#{msg['channel']} - {msg['user']}: {msg['text'][:100]}...")
        print()
