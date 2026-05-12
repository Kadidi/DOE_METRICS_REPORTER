"""SF API tool — wraps query_sfapi.py for use by the agent."""

from typing import Any


class SFAPITool:
    """Tool for querying NERSC Superfacility API.

    Covers: system status, planned/unplanned outages, SWOs, maintenance windows.
    No authentication required for public endpoints.
    """

    schema = {
        "name": "query_sfapi",
        "description": (
            "Query the NERSC Superfacility API for real-time and scheduled information. "
            "Use this tool for: current system status (perlmutter, doudna, HPSS, CFS, globus), "
            "active or upcoming planned maintenance windows, unplanned/emergency outages, "
            "system-wide outages (SWO), and recent outage history. "
            "Always call this tool FIRST for any question about current system state or outages "
            "before searching other sources."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "Natural language question about NERSC systems. Examples: "
                        "'What is the current status of Perlmutter?', "
                        "'Are there any unplanned outages?', "
                        "'What maintenance is scheduled this month?', "
                        "'What was the last SWO?'"
                    )
                }
            },
            "required": ["question"]
        }
    }

    def execute(self, inputs: dict) -> str:
        """Run the SF API query.

        Args:
            inputs: dict with 'question' key

        Returns:
            Formatted string with SF API response
        """
        try:
            from query_sfapi import query_sfapi
        except ImportError:
            return "SF API unavailable: sfapi_client not installed. Run: pip install sfapi_client"

        question = inputs.get("question", "")
        if not question:
            return "Error: 'question' input is required for query_sfapi tool."

        result = query_sfapi(question)

        if "error" in result.get("raw", {}):
            return f"SF API error: {result['raw']['error']}"

        return result.get("answer", "No answer returned from SF API.")
