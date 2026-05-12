"""
Tools registry for DOE Metrics Reporter agent.

Each tool wraps an existing query_*.py module and exposes:
  - SCHEMA: the JSON schema the LLM uses to decide when/how to call the tool
  - execute(input: dict) -> str: runs the tool and returns a string result

The LLM never imports query_*.py directly — it only sees the schemas.
The agent loop calls execute() after the LLM picks a tool.

Adding a new source:
  1. Create tools/your_source_tool.py following the pattern below
  2. Import it here and add to TOOL_REGISTRY and TOOL_SCHEMAS
"""

from tools.sfapi_tool import SFAPITool
from tools.slack_tool import SlackTool
from tools.gmail_tool import GmailTool
from tools.docs_tool import DocsTool
from tools.utilization_tool import UtilizationTool, UtilizationTrendTool
from tools.investigation_tool import InvestigationTool

# Registry: tool name → tool instance
TOOL_REGISTRY = {
    "query_sfapi":    SFAPITool(),
    "search_slack":   SlackTool(),
    "search_gmail":   GmailTool(),
    "search_docs":    DocsTool(),
    "report_utilization": UtilizationTool(),
    "analyze_utilization_trend": UtilizationTrendTool(),
    "investigate_utilization_drop": InvestigationTool(),
}

# Schemas: passed directly to the LLM in every request
# The LLM reads these descriptions to decide which tool to call
TOOL_SCHEMAS = [tool.schema for tool in TOOL_REGISTRY.values()]


def execute_tool(name: str, inputs: dict) -> str:
    """Execute a tool by name with given inputs.

    Args:
        name:   Tool name matching a key in TOOL_REGISTRY
        inputs: Dict of inputs matching the tool's input_schema

    Returns:
        String result from the tool, or error message if tool not found
    """
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return f"Unknown tool: '{name}'. Available tools: {list(TOOL_REGISTRY.keys())}"
    return tool.execute(inputs)
