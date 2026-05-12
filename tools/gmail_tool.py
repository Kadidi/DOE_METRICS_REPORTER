"""Gmail tool — wraps query_gmail.py for use by the agent."""


class GmailTool:
    """Tool for searching NERSC outage and RCA emails.

    Covers: RCA emails from CSG team members, outage notifications,
    maintenance announcements sent to NERSC internal mailing lists.
    """

    # NERSC systems to recognize in queries
    NERSC_SYSTEMS = ["perlmutter", "doudna", "hpss", "cfs", "dtns", "spin", "globus"]

    schema = {
        "name": "search_gmail",
        "description": (
            "Search Gmail for NERSC outage reports and root cause analysis (RCA) emails. "
            "These emails are sent by NERSC CSG team members to internal mailing lists "
            "and contain detailed explanations of what caused an outage, what failed, "
            "and what was done to fix it. "
            "Use this tool when the user asks WHY something happened, wants a root cause, "
            "or needs the full explanation of an incident — AFTER using query_sfapi "
            "to identify which outage to look for. "
            "The search covers the last 30 days by default."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "description": (
                        "NERSC system name to search for in email subjects. "
                        "Examples: 'perlmutter', 'doudna', 'HPSS', 'CFS'. "
                        "Use the system name returned by query_sfapi."
                    )
                },
                "date_after": {
                    "type": "string",
                    "description": (
                        "Search for emails after this date. "
                        "Format: YYYY/MM/DD. Use the outage start date from SF API minus 1-2 days."
                    )
                },
                "date_before": {
                    "type": "string",
                    "description": (
                        "Search for emails before this date. "
                        "Format: YYYY/MM/DD. Use the outage end date from SF API plus 1-2 days."
                    )
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Additional subject keywords to narrow the search. "
                        "Examples: ['SWO', 'outage', 'maintenance', 'RCA']. "
                        "Combined with system name automatically."
                    )
                },
                "days_back": {
                    "type": "integer",
                    "description": (
                        "How many days back to search if no specific dates given. "
                        "Default is 30."
                    ),
                    "default": 30
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails to return. Default is 5.",
                    "default": 5
                }
            },
            "required": []
        }
    }

    def execute(self, inputs: dict) -> str:
        """Run the Gmail search.

        Args:
            inputs: dict with optional 'system', 'date_after', 'date_before',
                    'keywords', 'days_back', 'max_results'

        Returns:
            Formatted string with email results including body previews
        """
        try:
            from query_gmail import GmailQuerier, HAS_GMAIL_API
        except ImportError:
            return "Gmail unavailable: query_gmail.py not found."

        if not HAS_GMAIL_API:
            return "Gmail unavailable: google-api-python-client not installed."

        system = inputs.get("system", "")
        date_after = inputs.get("date_after", "")
        date_before = inputs.get("date_before", "")
        keywords = inputs.get("keywords", [])
        days_back = inputs.get("days_back", 30)
        max_results = inputs.get("max_results", 5)

        # Build Gmail query
        query_parts = []

        # Subject filter: system name + RCA keywords
        subject_terms = list(keywords) if keywords else []
        if system:
            subject_terms.insert(0, system)
        if not subject_terms:
            subject_terms = ["SWO", "perlmutter", "doudna", "HPSS", "CFS",
                             "maintenance", "outage"]
        subject_filter = "subject:(" + " OR ".join(subject_terms) + ")"
        query_parts.append(subject_filter)

        # Date range
        if date_after:
            query_parts.append(f"after:{date_after}")
        if date_before:
            query_parts.append(f"before:{date_before}")
        if not date_after and not date_before:
            query_parts.append(f"newer_than:{days_back}d")

        query = " ".join(query_parts)

        try:
            querier = GmailQuerier()
            emails = querier.search_emails(query, max_results=max_results, include_body=True)

            if not emails:
                return f"No RCA emails found. Gmail query used: {query}"

            result = f"Found {len(emails)} RCA/outage email(s) (query: {query}):\n\n"
            for i, email in enumerate(emails, 1):
                result += f"{i}. From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                body = email.get("body", email.get("snippet", ""))[:600]
                if body:
                    result += f"   Content:\n{body}\n"
                result += "\n"

            return result

        except Exception as e:
            return f"Gmail error: {e}. Try running: python test_google_docs.py to re-authenticate."
