"""Slack tool — wraps query_slack.py for use by the agent."""


class SlackTool:
    """Tool for searching NERSC Slack channels.

    Covers: real-time team discussion, incident threads, HPC POC updates,
    general announcements. Best for finding human context around an event.
    """

    schema = {
        "name": "search_slack",
        "description": (
            "Search NERSC Slack channels for messages related to a topic. "
            "Use this tool to find: team discussion around an incident, "
            "HPC POC status updates, real-time commentary during an outage, "
            "announcements in #general, or technical discussion in #hpcpoc. "
            "Best used AFTER query_sfapi to get human context and team reaction "
            "to an outage or maintenance event. "
            "Available channels: #fire (incidents), #general (announcements), #hpcpoc (HPC discussion)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": (
                        "Slack channel name without #. "
                        "Use 'fire' for incidents/outages, "
                        "'hpcpoc' for HPC/Perlmutter discussion, "
                        "'general' for announcements."
                    )
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Keywords to filter messages. Use specific terms like "
                        "['perlmutter', 'outage'] or ['maintenance', 'february']. "
                        "Leave empty to get all recent messages."
                    )
                },
                "days_back": {
                    "type": "integer",
                    "description": "How many days back to search. Default is 7.",
                    "default": 7
                }
            },
            "required": ["channel"]
        }
    }

    def execute(self, inputs: dict) -> str:
        """Run the Slack query.

        Args:
            inputs: dict with 'channel', optional 'keywords' and 'days_back'

        Returns:
            Formatted string with Slack messages
        """
        try:
            from query_slack import SlackQuerier, HAS_SLACK_SDK
        except ImportError:
            return "Slack unavailable: query_slack.py not found."

        if not HAS_SLACK_SDK:
            return "Slack unavailable: slack-sdk not installed. Run: pip install slack-sdk"

        channel = inputs.get("channel", "")
        if not channel:
            return "Error: 'channel' input is required for search_slack tool."

        keywords = inputs.get("keywords", None)
        days_back = inputs.get("days_back", 7)

        try:
            querier = SlackQuerier()
            messages = querier.get_channel_messages(
                channel_name=channel,
                days_back=days_back,
                keywords=keywords if keywords else None
            )

            if not messages:
                return f"No messages found in #{channel} for the past {days_back} days."

            result = f"Found {len(messages)} message(s) in #{channel}:\n\n"
            for i, msg in enumerate(messages[:10], 1):
                result += f"{i}. {msg['text'][:300]}\n\n"

            return result

        except Exception as e:
            return f"Error querying Slack #{channel}: {e}"
