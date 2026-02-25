#!/usr/bin/env python3
"""Slack bot that answers questions using the existing multi-source agent."""

import os
import re
import time
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from config import get_slack_token
from multi_ask import multi_ask, HAS_ANTHROPIC, get_ai_api_key


def get_app_token() -> Optional[str]:
    """Get Slack app-level token for Socket Mode."""
    return os.getenv("SLACK_APP_TOKEN")


def clean_question(text: str, bot_user_id: str) -> str:
    """Strip mention and normalize user question text."""
    if not text:
        return ""

    # Remove bot mention like <@U123ABC>
    text = re.sub(rf"<@{re.escape(bot_user_id)}>", "", text)

    # Remove other mentions/extra whitespace
    text = re.sub(r"<@[^>]+>", "", text)
    return text.strip()


def format_agent_answer(result: dict) -> str:
    """Format multi_ask result to concise Slack output."""
    lines = []

    # SF API results (show first - usually most relevant for status questions)
    sfapi = result["sources"].get("sfapi", {})
    if sfapi.get("searched") and sfapi.get("results"):
        lines.append("*NERSC Systems*")
        for item in sfapi["results"][:2]:
            if "error" in item:
                lines.append(f"- Error: {item['error']}")
            else:
                answer = str(item.get("answer", "")).strip()
                # SF API answers already have formatting, use as-is but limit length
                if len(answer) > 500:
                    answer = answer[:500] + "..."
                lines.append(answer)

    # Google Docs results
    docs = result["sources"].get("google_docs", {})
    if docs.get("searched") and docs.get("results"):
        lines.append("*Google Docs*")
        for item in docs["results"][:2]:
            if "error" in item:
                lines.append(f"- {item['document']}: {item['error']}")
            else:
                answer = str(item["answer"]).strip().replace("\n", " ")
                lines.append(f"- {item['document']}: {answer[:300]}")

    # Slack results
    slack = result["sources"].get("slack", {})
    if slack.get("searched") and slack.get("results"):
        lines.append("*Slack*")
        for item in slack["results"][:2]:
            if "error" in item:
                lines.append(f"- Error: {item['error']}")
            else:
                summary = item.get("summary", "").strip().replace("\n", " ")
                lines.append(f"- #{item['channel']}: {summary[:300]}")

    if not lines:
        return "I couldn't find matching results in the configured sources."

    return "\n".join(lines)


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

    print(f"Slack bot online as {bot_name} ({bot_user_id})")
    print(f"Sources: Google Docs, Slack, SF API")
    
    if not (HAS_ANTHROPIC and get_ai_api_key()):
        print("Warning: ANTHROPIC_API_KEY/CBORG_API_KEY not set; using keyword mode")

    socket_client = SocketModeClient(app_token=app_token, web_client=web_client)

    def process(client: SocketModeClient, req: SocketModeRequest) -> None:
        if req.type != "events_api":
            return

        # Ack quickly to avoid retries
        client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

        payload = req.payload
        event = payload.get("event", {})
        print(
            "Received event:",
            event.get("type"),
            "channel_type=",
            event.get("channel_type"),
            "user=",
            event.get("user"),
        )

        if not should_reply(event, bot_user_id):
            print("Skipping event: does not match reply rules")
            return

        channel = event.get("channel")
        # Reply in-thread only when the message is already threaded.
        # For top-level mentions, respond in-channel for visibility.
        thread_ts = event.get("thread_ts")
        question = clean_question(event.get("text", ""), bot_user_id)

        if not channel:
            return

        if not question:
            try:
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text="Ask me a question after mentioning me, and I will search Google Docs, Slack, and NERSC SF API.",
                )
            except Exception:
                pass
            return

        try:
            # Add thinking indicator
            web_client.reactions_add(
                channel=channel,
                name="hourglass_flowing_sand",
                timestamp=event.get("ts")
            )
        except Exception:
            pass

        try:
            result = multi_ask(question, verbose=False)
            answer = format_agent_answer(result)

            web_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=answer,
            )
            print("Reply posted to channel", channel)
            
            # Remove thinking indicator
            try:
                web_client.reactions_remove(
                    channel=channel,
                    name="hourglass_flowing_sand",
                    timestamp=event.get("ts")
                )
            except Exception:
                pass
                
        except SlackApiError as e:
            err = getattr(e, "response", None)
            if err is not None:
                print(f"Slack API error: {err.get('error', e)}")
            else:
                print(f"Slack API error: {e}")
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

    socket_client.socket_mode_request_listeners.append(process)
    socket_client.connect()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    run_bot()
