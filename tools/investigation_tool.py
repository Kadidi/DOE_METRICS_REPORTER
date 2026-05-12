"""Investigation tool for utilization drops."""

import json
from datetime import datetime, timedelta


class InvestigationTool:
    """Investigate possible causes of utilization drops."""

    schema = {
        "name": "investigate_utilization_drop",
        "description": (
            "Investigate possible causes of a utilization drop using SFAPI, Gmail, and Slack. "
            "Use this after a utilization trend analysis shows utilization below threshold or a "
            "day-over-day decrease greater than 1 percentage point."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "enum": ["all", "gpu", "cpu"],
                    "description": "Perlmutter resource to investigate. Default may include both cpu and gpu.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format for the investigation window.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format for the investigation window.",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason the investigation was triggered.",
                },
            },
            "required": ["resource", "start_date", "end_date", "reason"],
        },
    }

    def execute(self, inputs: dict) -> str:
        """Investigate likely causes around the date range."""
        try:
            from query_sfapi import get_recent_outages
            from query_gmail import GmailQuerier, HAS_GMAIL_API
            from query_slack import SlackQuerier, HAS_SLACK_SDK
        except ImportError as exc:
            return json.dumps({"error": str(exc)})

        resource = inputs["resource"]
        start_date = inputs["start_date"]
        end_date = inputs["end_date"]
        reason = inputs["reason"]

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_back = max((datetime.utcnow() - start_dt).days + 2, 7)

        result = {
            "resource": resource,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "sfapi": None,
            "gmail": None,
            "slack": None,
        }

        outages = get_recent_outages(days=max(days_back, 14))
        if outages and isinstance(outages, list):
            filtered = []
            for outage in outages:
                start_at = outage.get("start_at", "")
                if start_at:
                    try:
                        when = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                        if start_dt - timedelta(days=1) <= when.replace(tzinfo=None) <= end_dt + timedelta(days=1):
                            filtered.append(outage)
                    except Exception:
                        continue
            result["sfapi"] = filtered[:10]

        if HAS_GMAIL_API:
            try:
                querier = GmailQuerier()
                after_date = (start_dt - timedelta(days=2)).strftime("%Y/%m/%d")
                before_date = (end_dt + timedelta(days=2)).strftime("%Y/%m/%d")
                gmail_query = (
                    f"after:{after_date} before:{before_date} "
                    "subject:(perlmutter OR outage OR maintenance OR SWO OR utilization)"
                )
                emails = querier.search_emails(gmail_query, max_results=5, include_body=True)
                result["gmail"] = [
                    {
                        "from": email.get("from"),
                        "subject": email.get("subject"),
                        "date": email.get("date"),
                        "snippet": email.get("snippet"),
                    }
                    for email in emails
                ]
            except Exception as exc:
                result["gmail"] = {"error": str(exc)}
        else:
            result["gmail"] = {"error": "Gmail API unavailable"}

        if HAS_SLACK_SDK:
            try:
                querier = SlackQuerier()
                keywords = ["perlmutter", resource, "outage", "maintenance", "queue"]
                slack_results = {}
                for channel in ["fire", "hpcpoc"]:
                    messages = querier.get_channel_messages(channel, days_back=days_back, keywords=keywords)
                    slack_results[channel] = [
                        {
                            "text": msg.get("text"),
                            "timestamp": msg.get("timestamp"),
                            "thread_ts": msg.get("thread_ts"),
                        }
                        for msg in messages[:10]
                    ]
                result["slack"] = slack_results
            except Exception as exc:
                result["slack"] = {"error": str(exc)}
        else:
            result["slack"] = {"error": "Slack SDK unavailable"}

        return json.dumps(result)
