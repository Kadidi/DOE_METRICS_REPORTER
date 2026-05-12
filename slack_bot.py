#!/usr/bin/env python3
"""Slack bot that answers questions using the agentic multi-source agent."""

import os
import re
import time
from typing import Optional

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from config import get_slack_token

# ── NEW: import agent_ask instead of multi_ask ───────────────────────────────
from agent_ask import agent_ask

load_dotenv()


def get_app_token() -> Optional[str]:
    """Get Slack app-level token for Socket Mode."""
    return os.getenv("SLACK_APP_TOKEN")


def clean_question(text: str, bot_user_id: str) -> str:
    """Strip mention and normalize user question text."""
    if not text:
        return ""
    text = re.sub(rf"<@{re.escape(bot_user_id)}>", "", text)
    text = re.sub(r"<@[^>]+>", "", text)
    return text.strip()


def should_reply(event: dict, bot_user_id: str) -> bool:
    """Decide if this event should trigger an agent response."""
    event_type = event.get("type")

    if event_type == "app_mention":
        return True

    if event_type != "message":
        return False

    if event.get("subtype"):
        return False

    if event.get("bot_id"):
        return False

    channel_type = event.get("channel_type")
    if channel_type == "im":
        return True

    text = event.get("text", "")
    return f"<@{bot_user_id}>" in text


def run_bot() -> None:
    """Start Socket Mode Slack bot."""
    bot_token = get_slack_token()
    app_token = get_app_token()

    if not bot_token:
        raise ValueError("Missing SLACK_BOT_TOKEN (or central .slack_token)")
    if not app_token:
        raise ValueError("Missing SLACK_APP_TOKEN (xapp-...) for Socket Mode")

    web_client = WebClient(token=bot_token)
    auth = web_client.auth_test()
    bot_user_id = auth["user_id"]
    bot_name = auth.get("user", "agent")

    provider = os.getenv("LLM_PROVIDER", "openai").upper()
    print(f"Slack bot online as {bot_name} ({bot_user_id})")
    print(f"LLM provider: {provider}")
    print("Sources: SF API, Slack, Gmail, Google Docs, utilization-calculation")

    socket_client = SocketModeClient(app_token=app_token, web_client=web_client)

    def process(client: SocketModeClient, req: SocketModeRequest) -> None:
        if req.type != "events_api":
            return

        # Ack quickly to avoid Slack retries
        client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

        payload = req.payload
        event = payload.get("event", {})
        print(
            "Received event:",
            event.get("type"),
            "channel_type=", event.get("channel_type"),
            "user=", event.get("user"),
        )

        if not should_reply(event, bot_user_id):
            print("Skipping event: does not match reply rules")
            return

        channel = event.get("channel")
        thread_ts = event.get("thread_ts")
        question = clean_question(event.get("text", ""), bot_user_id)

        if not channel:
            return

        if not question:
            try:
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=(
                        "Ask me a question and I'll search SF API, Slack, Gmail, "
                        "Google Docs, and utilization data to find the answer."
                    ),
                )
            except Exception:
                pass
            return

        # Add thinking indicator
        try:
            web_client.reactions_add(
                channel=channel,
                name="hourglass_flowing_sand",
                timestamp=event.get("ts")
            )
        except Exception:
            pass

        try:
            # ── NEW: agent_ask returns a plain string answer ─────────────────
            # verbose=False suppresses reasoning steps from printing to terminal
            answer = agent_ask(question, verbose=False)

            # Slack has a 4000 char limit per message — truncate if needed
            if len(answer) > 3900:
                answer = answer[:3900] + "\n\n_(truncated — ask a more specific question)_"

            web_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=answer,
            )
            print(f"Reply posted to channel {channel}")

        except SlackApiError as e:
            err = getattr(e, "response", None)
            print(f"Slack API error: {err.get('error', e) if err else e}")
        except Exception as e:
            print(f"Agent error: {e}")
            try:
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"I hit an error while answering: {e}",
                )
            except Exception:
                pass
        finally:
            # Always remove thinking indicator
            try:
                web_client.reactions_remove(
                    channel=channel,
                    name="hourglass_flowing_sand",
                    timestamp=event.get("ts")
                )
            except Exception:
                pass

    socket_client.socket_mode_request_listeners.append(process)
    socket_client.connect()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    run_bot()
