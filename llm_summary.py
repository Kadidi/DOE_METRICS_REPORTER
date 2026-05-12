#!/usr/bin/env python3
"""Cross-source prompt building and result normalization for AI summaries."""

from typing import Dict, List, Optional

from config import get_ai_api_key
from ask_document import ask_llm


def _truncate(text: str, limit: int = 800) -> str:
    """Trim long source payloads before prompting."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def normalize_query_results(results: Dict) -> Dict[str, List[str]]:
    """Extract compact, source-labeled evidence from multi_ask results."""
    sources = results.get("sources", {})
    normalized = {"sfapi": [], "slack": [], "google_docs": []}

    for entry in sources.get("sfapi", {}).get("results", []):
        if entry.get("error"):
            normalized["sfapi"].append(f"Error: {entry['error']}")
        else:
            normalized["sfapi"].append(_truncate(entry.get("answer", "")))

    for entry in sources.get("slack", {}).get("results", []):
        if entry.get("error"):
            normalized["slack"].append(f"Error: {entry['error']}")
            continue

        channel = entry.get("channel", "unknown")
        summary = _truncate(entry.get("summary", ""), limit=1000)
        normalized["slack"].append(f"Channel #{channel}\n{summary}")

    for entry in sources.get("google_docs", {}).get("results", []):
        document = entry.get("document", "Document")
        if entry.get("error"):
            normalized["google_docs"].append(f"{document}: Error: {entry['error']}")
        else:
            normalized["google_docs"].append(
                f"{document}\n{_truncate(entry.get('answer', ''), limit=1000)}"
            )

    return normalized


def build_combined_summary_prompt(question: str, normalized_results: Dict[str, List[str]]) -> tuple[str, str]:
    """Build system and user prompts for cross-source synthesis."""
    system_prompt = """You are an operations analyst for NERSC system-status questions.

Your task is to answer the user's question using the provided source results.

Source priority for current/live status:
1. SF API
2. Slack
3. Google Docs

Rules:
- Treat SF API as authoritative for current system status.
- Treat Slack as recent operational context, not final authority.
- Treat Google Docs as historical reference, not real-time status.
- Do not invent facts not present in the sources.
- If sources conflict, state the conflict explicitly and prefer the higher-priority source.
- If the answer is uncertain, say what is known and what is unknown.
- Use concrete dates when mentioning historical events.
- Keep the answer concise and operationally useful.
"""

    sfapi_text = "\n\n".join(normalized_results.get("sfapi", [])) or "No SF API results."
    slack_text = "\n\n".join(normalized_results.get("slack", [])) or "No Slack results."
    docs_text = "\n\n".join(normalized_results.get("google_docs", [])) or "No Google Docs results."

    user_prompt = f"""User question:
{question}

Summarize the combined results from all queried sources.

Return exactly these sections:
Answer:
A short direct answer to the user's question.

Why:
2-4 sentences explaining the answer using source priority.

Evidence:
- SF API: ...
- Slack: ...
- Google Docs: ...

Conflicts:
State any disagreement between sources, or say "None".

Sources used:
List only the sources that actually returned results.

SF API results:
{sfapi_text}

Slack results:
{slack_text}

Google Docs results:
{docs_text}
"""
    return system_prompt, user_prompt


def summarize_query_results(question: str, results: Dict) -> Optional[str]:
    """Generate a top-level AI summary across all source results."""
    if not get_ai_api_key():
        return None

    normalized_results = normalize_query_results(results)
    if not any(normalized_results.values()):
        return None

    system_prompt, user_prompt = build_combined_summary_prompt(question, normalized_results)
    summary = ask_llm(user_prompt, system_prompt=system_prompt)
    if summary.startswith("Error:") or summary.startswith("Error calling AI API"):
        return None
    return summary.strip()
