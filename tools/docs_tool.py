"""Docs tool — wraps ask_document.py for use by the agent."""

import os
import yaml
from pathlib import Path


class DocsTool:
    """Tool for querying NERSC Google Docs.

    Covers: historical downtime records, scheduled maintenance logs,
    incident archives. Best for questions about past events that
    predate the SF API outage history window.
    """

    schema = {
        "name": "search_docs",
        "description": (
            "Search NERSC Google Docs for historical downtime and incident records. "
            "Use this tool when: the user asks about past outages by month or date range, "
            "wants a summary of incidents over a period, or needs details not available "
            "in the SF API (which has a limited history window). "
            "Currently indexed: NERSC Downtimes (Sept-Dec) — covers Perlmutter downtime "
            "records from September through February. "
            "Use query_sfapi first for recent/current status, then use this tool "
            "for historical context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "Natural language question to ask the document. Examples: "
                        "'What unplanned outages happened in December?', "
                        "'How many maintenance windows were there in October?', "
                        "'What caused the February 5th outage?'"
                    )
                },
                "doc_name": {
                    "type": "string",
                    "description": (
                        "Optional: specific document name to query. "
                        "If not provided, searches all configured documents. "
                        "Available: 'NERSC Downtimes (Sept-Dec)'"
                    )
                }
            },
            "required": ["question"]
        }
    }

    def _load_doc_configs(self) -> list:
        """Load document configs from documents_config.yaml."""
        try:
            from config import get_config_path
            config_path = get_config_path()
        except ImportError:
            config_path = "documents_config.yaml"

        if not Path(config_path).exists():
            return []

        with open(config_path) as f:
            config = yaml.safe_load(f)

        return config.get("google_docs", [])

    def execute(self, inputs: dict) -> str:
        """Run the Google Docs query.

        Args:
            inputs: dict with 'question' and optional 'doc_name'

        Returns:
            Formatted string with answers from matching documents
        """
        try:
            from test_google_docs import get_credentials
            from ask_document import get_document_content, ask_document_with_claude, ask_document_simple
        except ImportError as e:
            return f"Google Docs unavailable: {e}"

        question = inputs.get("question", "")
        if not question:
            return "Error: 'question' input is required for search_docs tool."

        doc_name_filter = inputs.get("doc_name", "")

        # Determine if AI is available
        use_ai = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("CBORG_API_KEY"))

        # Load doc configs
        docs = self._load_doc_configs()
        if not docs:
            return "No Google Docs configured. Check documents_config.yaml."

        # Filter by doc_name if specified
        if doc_name_filter:
            docs = [d for d in docs if doc_name_filter.lower() in d["name"].lower()]
            if not docs:
                return f"No document found matching '{doc_name_filter}'."

        try:
            creds = get_credentials()
        except Exception as e:
            return f"Google auth error: {e}. Run: python test_google_docs.py"

        results = []
        for doc in docs:
            doc_id = doc["id"]
            doc_name = doc["name"]

            title, content = get_document_content(creds, doc_id)
            if not content:
                results.append(f"{doc_name}: Could not fetch document.")
                continue

            if use_ai:
                answer = ask_document_with_claude(title, content, question)
            else:
                answer = ask_document_simple(title, content, question)

            results.append(f"{doc_name}:\n{answer}")

        return "\n\n".join(results) if results else "No results found in Google Docs."
