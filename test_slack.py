#!/usr/bin/env python3
"""Test Slack authentication and API access."""

import os
import sys

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("❌ slack-sdk not installed")
    print("Run: pip install --user slack-sdk")
    sys.exit(1)

def test_slack_auth():
    """Test Slack authentication and basic API access."""

    print("=" * 80)
    print("Slack Authentication Test")
    print("=" * 80)
    print()

    # Check if token is set
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        print()
        print("To set it:")
        print("  export SLACK_BOT_TOKEN='xoxb-your-token-here'")
        print()
        print("To get a token:")
        print("  1. Go to https://api.slack.com/apps")
        print("  2. Create a new app or select existing")
        print("  3. Go to 'OAuth & Permissions'")
        print("  4. Add bot token scopes:")
        print("     - channels:history")
        print("     - channels:read")
        print("     - search:read")
        print("     - users:read")
        print("  5. Install app to workspace")
        print("  6. Copy 'Bot User OAuth Token' (starts with xoxb-)")
        print()
        return False

    print(f"✓ SLACK_BOT_TOKEN found")
    print(f"  Token: {token[:15]}...")
    print()

    # Initialize client
    client = WebClient(token=token)

    # Test 1: Auth test
    print("Test 1: Testing authentication...")
    try:
        response = client.auth_test()
        print("✓ Authentication successful!")
        print(f"  Workspace: {response['team']}")
        print(f"  Bot user: {response['user']}")
        print(f"  Bot ID: {response['user_id']}")
        print()
    except SlackApiError as e:
        print(f"❌ Authentication failed: {e.response['error']}")
        print(f"   {e}")
        return False

    # Test 2: List channels
    print("Test 2: Listing channels...")
    try:
        response = client.conversations_list(
            exclude_archived=True,
            types="public_channel",
            limit=10
        )
        channels = response["channels"]
        print(f"✓ Found {len(channels)} channel(s)")
        print()
        print("Available channels:")
        for ch in channels[:10]:
            member_count = ch.get('num_members', 0)
            topic = ch.get('topic', {}).get('value', 'No topic')
            print(f"  #{ch['name']:<20} ({member_count} members) - {topic[:50]}")
        print()
    except SlackApiError as e:
        print(f"❌ Failed to list channels: {e.response['error']}")
        print(f"   Make sure the bot has 'channels:read' scope")
        return False

    # Test 3: Try to read a channel
    if channels:
        test_channel = channels[0]
        print(f"Test 3: Reading messages from #{test_channel['name']}...")
        try:
            response = client.conversations_history(
                channel=test_channel['id'],
                limit=5
            )
            messages = response.get("messages", [])
            print(f"✓ Successfully read {len(messages)} message(s)")
            if messages:
                print()
                print("Recent messages:")
                for i, msg in enumerate(messages[:3], 1):
                    text = msg.get('text', '(no text)')
                    print(f"  {i}. {text[:100]}")
            print()
        except SlackApiError as e:
            print(f"⚠️  Could not read messages: {e.response['error']}")
            print(f"   This is normal if bot is not in the channel")
            print(f"   Invite bot to channel: /invite @{response['user']}")
            print()

    # Test 4: Search capability
    print("Test 4: Testing search...")
    try:
        response = client.search_messages(
            query="test",
            count=1
        )
        print("✓ Search working!")
        total = response.get("messages", {}).get("total", 0)
        print(f"  Found {total} result(s) for 'test'")
        print()
    except SlackApiError as e:
        print(f"⚠️  Search failed: {e.response['error']}")
        print(f"   Make sure bot has 'search:read' scope")
        print()

    # Summary
    print("=" * 80)
    print("✓ Slack connection test complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Invite bot to channels you want to query:")
    print(f"     /invite @{response['user']}")
    print("  2. Test querying:")
    print("     python query_slack.py 'your search query'")
    print("  3. Use multi-source search:")
    print("     python multi_ask.py 'your question'")
    print()

    return True


if __name__ == "__main__":
    success = test_slack_auth()
    sys.exit(0 if success else 1)
