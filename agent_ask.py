#!/usr/bin/env python3
"""
DOE Metrics Reporter — Agentic Q&A entry point.

Replaces the keyword-routing in multi_ask.py with a proper ReAct agent loop:
  Reason → Act (call a tool) → Observe (read result) → repeat until done.

The LLM decides which tools to call, in what order, based on the question.
No hardcoded routing rules needed.

LLM portability:
  Set LLM_PROVIDER env var to switch backends:
    export LLM_PROVIDER=openai    # Codex (default)
    export LLM_PROVIDER=cborg     # NERSC CBORG
    export LLM_PROVIDER=anthropic # Claude direct

Usage:
  python agent_ask.py "Why did Perlmutter go down last week?"
  python agent_ask.py   # interactive mode
"""

import os
import sys
import json
from typing import Optional

# ---------------------------------------------------------------------------
# LLM client — lightweight adapter layer for provider portability
# ---------------------------------------------------------------------------

def _get_llm_client():
    """Return an OpenAI-compatible client based on LLM_PROVIDER env var.

    Supports:
      openai    — Codex / OpenAI API
      cborg     — NERSC CBORG (OpenAI-compatible)
      anthropic — Claude direct (via openai-compatible shim)

    All providers use the same OpenAI client since CBORG and most
    self-hosted LLMs expose an OpenAI-compatible endpoint.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)

    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "cborg":
        api_key = os.getenv("CBORG_API_KEY")
        base_url = os.getenv("CBORG_BASE_URL", "https://api.cborg.lbl.gov/v1")
        if not api_key:
            print("ERROR: CBORG_API_KEY not set.")
            sys.exit(1)
        return OpenAI(api_key=api_key, base_url=base_url), _get_model_name(provider)

    elif provider == "anthropic":
        # Use Anthropic via openai-compatible shim
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = "https://api.anthropic.com/v1"
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY not set.")
            sys.exit(1)
        return OpenAI(api_key=api_key, base_url=base_url), _get_model_name(provider)

    else:
        # Default: OpenAI / Codex
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY not set.")
            sys.exit(1)
        return OpenAI(api_key=api_key), _get_model_name(provider)


def _get_model_name(provider: str) -> str:
    """Get the model name for a given provider.

    Can be overridden with LLM_MODEL env var.
    """
    if os.getenv("LLM_MODEL"):
        return os.getenv("LLM_MODEL")

    defaults = {
        "openai":    "gpt-4o",
        "cborg":     "lbl/cborg-coder-v1",
        "anthropic": "claude-sonnet-4-5",
    }
    return defaults.get(provider, "gpt-4o")


# ---------------------------------------------------------------------------
# System prompt — defines agent behavior and tool usage guidelines
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the DOE Metrics Reporter agent for NERSC (National Energy Research Scientific Computing Center).

Your job is to answer questions about NERSC system operations by querying the right data sources.

## Available Tools
- query_sfapi: Real-time system status, planned/unplanned outages, SWOs, maintenance windows
- search_slack: Team discussion in Slack channels (#fire for incidents, #hpcpoc for HPC)
- search_gmail: RCA emails from NERSC CSG team with root cause explanations
- search_docs:  Historical downtime records in Google Docs
- report_utilization: Daily or monthly Perlmutter CPU/GPU utilization from IRIS usage data
- analyze_utilization_trend: Past-7-day utilization trend analysis with investigation triggers
- investigate_utilization_drop: Root-cause investigation for low or falling utilization

## Tool Usage Guidelines
1. For STATUS questions (is X up/down, current state):
   → Call query_sfapi first. If it answers clearly, you may stop there.

2. For ROOT CAUSE / RCA questions (why did X happen, what caused it):
   → Call query_sfapi first to identify the outage (system name, date, description)
   → Then call search_gmail with the system name and date range from SF API
   → Then call search_slack if more context is needed

3. For HISTORICAL questions (what happened in December, last month's outages):
   → Call search_docs first (has detailed historical records)
   → Call query_sfapi first to identify the outage (system name, date, description)
   → Then call search_gmail with the system name and date range from SF API
   → Then call search_slack if more context is needed
   → Supplement with query_sfapi for recent history

4. For PLANNED MAINTENANCE:
   → Call query_sfapi (has the full schedule)

5. For TEAM DISCUSSION / ANNOUNCEMENTS:
   → Call search_slack (skip SF API and Gmail)

6. For UTILIZATION questions (daily/monthly CPU or GPU utilization, percentages, usage metrics):
   → Call report_utilization
   → Use mode='day' for a single day and mode='month' for monthly summaries
   → Default to resource='all' unless the user explicitly asks for CPU or GPU
   → If the user asks whether the result differs from Gabor's daily utilization email, set compare_with_gabor=true

7. For UTILIZATION TREND questions (past 7 days, recent trend, whether utilization is declining):
   → Call analyze_utilization_trend first
   → If investigation_required=true, call investigate_utilization_drop with the reported date window and trigger reason
   → Summarize both the trend and the likely causes from the investigation output

## Response Guidelines
- Always cite which source provided each piece of information
- If a tool returns an error, note it and continue with other sources
- If you cannot find the answer after using relevant tools, say so clearly
- Be concise but complete — this output may go to DOE management reports
- Include specific details: dates, times, system names, durations
- For utilization answers, include the exact date or month and specify whether the figure is CPU or GPU
- If a Gabor comparison is available, report both the absolute difference in percentage points and the relative percent difference
- For trend answers, report the 7-day direction clearly and explain whether investigation was triggered
"""


# ---------------------------------------------------------------------------
# ReAct agent loop
# ---------------------------------------------------------------------------

def agent_ask(question: str, verbose: bool = True, max_steps: int = 8) -> str:
    """Ask a question using the ReAct agent loop.

    The LLM reasons about the question, calls tools as needed,
    observes results, and continues until it has a complete answer
    or reaches max_steps.

    Args:
        question:  Natural language question
        verbose:   Print reasoning steps and tool calls
        max_steps: Maximum tool calls before forcing a final answer

    Returns:
        Final answer string from the agent
    """
    from tools import TOOL_SCHEMAS, execute_tool

    client, model = _get_llm_client()

    if verbose:
        print("=" * 80)
        print(f"DOE Metrics Reporter — Agent Mode ({os.getenv('LLM_PROVIDER', 'openai').upper()})")
        print("=" * 80)
        print(f"Question: {question}")
        print(f"Model:    {model}")
        print("=" * 80)
        print()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": question}
    ]

    step = 0

    while step < max_steps:
        step += 1

        if verbose:
            print(f"[Step {step}] Calling LLM...")

        response = client.chat.completions.create(
            model=model,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            messages=messages
        )

        message = response.choices[0].message

        # ── Agent is done — no more tool calls ──────────────────────────────
        if not message.tool_calls:
            final_answer = message.content or "No answer generated."
            if verbose:
                print()
                print("=" * 80)
                print("Final Answer:")
                print("=" * 80)
                print(final_answer)
                print("=" * 80)
            return final_answer

        # ── Agent wants to call tools ────────────────────────────────────────
        messages.append(message)  # add assistant message with tool_calls

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_inputs = json.loads(tool_call.function.arguments)

            if verbose:
                print(f"[Step {step}] Tool call: {tool_name}")
                print(f"           Inputs: {json.dumps(tool_inputs, indent=2)}")

            # Execute the tool
            tool_result = execute_tool(tool_name, tool_inputs)

            if verbose:
                preview = tool_result[:300].replace("\n", " ")
                print(f"           Result: {preview}...")
                print()

            # Feed result back to the LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

    # ── Hit max steps — ask for final answer with what we have ───────────────
    if verbose:
        print(f"[Max steps reached: {max_steps}] Requesting final answer...")

    messages.append({
        "role": "user",
        "content": "Please provide your final answer based on the information gathered so far."
    })

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    final_answer = response.choices[0].message.content or "Could not generate a final answer."

    if verbose:
        print()
        print("=" * 80)
        print("Final Answer:")
        print("=" * 80)
        print(final_answer)
        print("=" * 80)

    return final_answer


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive_mode():
    """Run interactive agent Q&A."""
    provider = os.getenv("LLM_PROVIDER", "openai").upper()

    print()
    print("=" * 80)
    print(f"DOE Metrics Reporter — Agent Mode ({provider})")
    print("=" * 80)
    print()
    print("Ask questions about NERSC systems. The agent will decide which")
    print("sources to query (SF API, Gmail, Slack, Google Docs) automatically.")
    print()
    print("Example questions:")
    print("  - What is the current status of Perlmutter?")
    print("  - Why did Perlmutter go down last week?")
    print("  - What unplanned outages happened in December?")
    print("  - Is there any maintenance scheduled this month?")
    print()
    print("Type 'quit' to exit")
    print("=" * 80)
    print()

    while True:
        try:
            question = input("❓ Your question: ").strip()
            if not question:
                continue
            if question.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break
            print()
            agent_ask(question, verbose=True)
            print()
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

        if question in ["--help", "-h", "help"]:
            print("""
DOE Metrics Reporter — Agent Mode

USAGE:
  python agent_ask.py "Your question"   # Single question
  python agent_ask.py                   # Interactive mode

SETUP:
  # Choose your LLM provider:
  export LLM_PROVIDER=openai            # Codex (default)
  export LLM_PROVIDER=cborg             # NERSC CBORG
  export LLM_PROVIDER=anthropic         # Claude direct

  # Set the matching API key:
  export OPENAI_API_KEY=your-key        # for openai
  export CBORG_API_KEY=your-key         # for cborg
  export ANTHROPIC_API_KEY=your-key     # for anthropic

  # Optional: override model
  export LLM_MODEL=gpt-4o

EXAMPLES:
  python agent_ask.py "What is the status of Perlmutter?"
  python agent_ask.py "Why did Perlmutter go down last week?"
  python agent_ask.py "What outages happened in December?"
  python agent_ask.py "Any maintenance scheduled this month?"
            """)
            return

        agent_ask(question, verbose=True)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
