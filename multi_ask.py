#!/usr/bin/env python3
"""Multi-source Q&A system that queries Google Docs, Slack, AND NERSC SF API automatically.

Routing is driven by priority_rules in documents_config.yaml:
  - priority: reorder and filter sources per question type
  - chain:    use SF API output to enrich the query to the next source (RCA mode)
"""

import sys
import os
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from query_slack import search_slack_simple, SlackQuerier, HAS_SLACK_SDK

# Import central config
try:
    from config import get_config_path, get_slack_token
except ImportError:
    def get_config_path():
        return "documents_config.yaml"
    def get_slack_token():
        return os.getenv("SLACK_BOT_TOKEN")

# Google Docs dependencies are optional at runtime.
try:
    from test_google_docs import get_credentials
    from ask_document import get_document_content, ask_document_with_claude, ask_document_simple
    HAS_GOOGLE_DOCS = True
except Exception:
    HAS_GOOGLE_DOCS = False

# SF API dependencies
try:
    from query_sfapi import (
        query_sfapi,
        get_all_systems_status,
        get_planned_outages,
        get_unplanned_outages,
        get_system_wide_outages,
        get_last_swo,
        HAS_SFAPI
    )
    HAS_SFAPI_MODULE = True
except ImportError:
    HAS_SFAPI_MODULE = False
    HAS_SFAPI = False

# Try to import anthropic
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_ai_api_key() -> Optional[str]:
    """Get AI API key from supported environment variables."""
    return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CBORG_API_KEY")


def _match_keywords(question: str, keywords: List[str]) -> List[str]:
    """Return which keywords from a list appear in the question (lowercase)."""
    q = question.lower()
    return [kw for kw in keywords if kw.lower() in q]


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

class MultiSourceRouter:
    """Routes queries to Google Docs, Slack, and SF API based on priority rules."""

    ALL_SOURCES = ["sfapi", "google_docs", "slack", "gmail"]

    def __init__(self, config_file=None):
        if config_file is None:
            config_file = get_config_path()

        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.google_docs = self.config.get("google_docs", [])
        self.slack_channels = self.config.get("slack_channels", [])
        self.sfapi_config = self.config.get("sfapi", {"enabled": True})
        self.strategy = self.config.get("search_strategy", {})
        self.priority_rules = self.strategy.get("priority_rules", [])

    def _load_config(self) -> dict:
        if not self.config_file.exists():
            print(f"Warning: Config file {self.config_file} not found")
            return {
                "google_docs": [],
                "slack_channels": [],
                "sfapi": {"enabled": True},
                "search_strategy": {
                    "sources": ["sfapi", "google_docs", "slack"],
                    "mode": "smart",
                    "max_per_source": 2
                }
            }
        with open(self.config_file) as f:
            return yaml.safe_load(f)

    def _score_source(self, source: Dict, question: str) -> int:
        """Score how relevant a source config is to the question."""
        return len(_match_keywords(question, source.get("keywords", [])))

    # ------------------------------------------------------------------
    # Priority rule matching
    # ------------------------------------------------------------------

    def match_priority_rule(self, question: str) -> Optional[Dict]:
        """Return the first priority rule whose keywords match the question.

        Returns the rule dict, or None if no rule matches.
        """
        for rule in self.priority_rules:
            keywords = rule.get("keywords", [])
            if _match_keywords(question, keywords):
                return rule
        return None

    def get_source_order(self, question: str) -> List[str]:
        """Return the ordered list of sources to query for this question.

        Uses priority_rules if a match is found, otherwise falls back to
        the default sources list in search_strategy.
        """
        rule = self.match_priority_rule(question)

        if rule:
            # Chain rules define their own step order
            if rule.get("strategy") == "chain":
                # Return all steps in order (step1 first, then step2 sources)
                order = [rule["chain_behavior"]["step1"]]
                order += rule["chain_behavior"].get("step2", [])
            else:
                order = rule.get("source_order", self.ALL_SOURCES)

            # Filter out sources explicitly skipped
            skip = rule.get("skip_sources", [])
            order = [s for s in order if s not in skip]

            # Filter out unavailable sources (gmail not built yet)
            order = self._filter_available(order, rule)
            return order

        # Default: use sources list from config
        return self.strategy.get("sources", ["sfapi", "google_docs", "slack"])

    def _filter_available(self, sources: List[str], rule: Dict) -> List[str]:
        """Remove sources that are unavailable, with graceful skip if configured."""
        skip_if_unavailable = rule.get("skip_sources_if_unavailable", [])
        available = []
        for src in sources:
            if src == "gmail":
                if src not in skip_if_unavailable:
                    # Only warn, don't crash
                    pass
                # Gmail not built yet — always skip silently
                continue
            available.append(src)
        return available

    def is_chain_question(self, question: str) -> bool:
        """Return True if the question matches a chain-strategy rule."""
        rule = self.match_priority_rule(question)
        return rule is not None and rule.get("strategy") == "chain"

    def get_chain_rule(self, question: str) -> Optional[Dict]:
        """Return the matching chain rule, or None."""
        rule = self.match_priority_rule(question)
        if rule and rule.get("strategy") == "chain":
            return rule
        return None

    # ------------------------------------------------------------------
    # Source selection
    # ------------------------------------------------------------------

    def should_search_source(self, source_name: str, question: str = "") -> bool:
        """Check if a source is in the ordered list for this question."""
        return source_name in self.get_source_order(question)

    def should_search_sfapi(self, question: str) -> bool:
        if not self.sfapi_config.get("enabled", True):
            return False
        return "sfapi" in self.get_source_order(question)

    def select_google_docs(self, question: str) -> List[Dict]:
        mode = self.strategy.get("mode", "smart")
        max_docs = self.strategy.get("max_per_source", 2)

        if mode == "all":
            return self.google_docs[:max_docs]
        elif mode == "first":
            return self.google_docs[:1] if self.google_docs else []
        else:  # smart
            scored = [(self._score_source(doc, question), doc) for doc in self.google_docs]
            scored = [(s, d) for s, d in scored if s > 0]
            scored.sort(key=lambda x: x[0], reverse=True)
            selected = [d for s, d in scored[:max_docs]]
            # Fallback: if nothing matched use default category or first doc
            if not selected and self.google_docs:
                default_cat = self.strategy.get("default_category")
                if default_cat:
                    selected = [d for d in self.google_docs if d.get("category") == default_cat]
                if not selected:
                    selected = [self.google_docs[0]]
            return selected

    def select_slack_channels(self, question: str) -> List[Dict]:
        mode = self.strategy.get("mode", "smart")
        max_channels = self.strategy.get("max_per_source", 2)

        if mode == "all":
            return self.slack_channels[:max_channels]
        elif mode == "first":
            return self.slack_channels[:1] if self.slack_channels else []
        else:  # smart
            scored = [(self._score_source(ch, question), ch) for ch in self.slack_channels]
            scored = [(s, c) for s, c in scored if s > 0]
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for s, c in scored[:max_channels]]

    def explain_routing(self, question: str) -> str:
        """Return a human-readable explanation of why sources were selected."""
        rule = self.match_priority_rule(question)
        order = self.get_source_order(question)

        lines = []
        if rule:
            matched_kw = _match_keywords(question, rule.get("keywords", []))
            strategy = rule.get("strategy", "priority")
            lines.append(f"📌 Rule matched: '{rule['name']}' (strategy: {strategy})")
            lines.append(f"   Triggered by: {matched_kw}")
            if strategy == "chain":
                chain = rule.get("chain_behavior", {})
                lines.append(f"   Step 1 → {chain.get('step1')} (get outage brief)")
                lines.append(f"   Step 2 → {chain.get('step2')} (find explanation)")
        else:
            lines.append("📌 No priority rule matched — using default source order")

        lines.append(f"   Source order: {' → '.join(order)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Source query helpers
# ---------------------------------------------------------------------------

def _query_sfapi_source(question: str, verbose: bool) -> Dict:
    """Query SF API and return a result dict."""
    if verbose:
        print("Querying NERSC Superfacility API...")
    try:
        sfapi_result = query_sfapi(question)
        answer = sfapi_result.get("answer", "No answer")
        if verbose:
            print(f"   ✅ SF API query complete\n")
        return {"source": "sfapi", "answer": answer, "raw": sfapi_result.get("raw", {})}
    except Exception as e:
        if verbose:
            print(f"   ❌ SF API error: {e}\n")
        return {"source": "sfapi", "error": str(e)}


def _query_google_docs_source(question: str, selected_docs: List[Dict],
                               use_ai: bool, verbose: bool) -> List[Dict]:
    """Query selected Google Docs and return list of result dicts."""
    results = []
    if not HAS_GOOGLE_DOCS:
        return [{"document": "Google Docs", "error": "Google Docs dependencies not installed"}]

    creds = get_credentials()
    for doc_config in selected_docs:
        doc_id = doc_config["id"]
        doc_name = doc_config["name"]
        if verbose:
            print(f"   Querying: {doc_name}...")
        title, content = get_document_content(creds, doc_id)
        if not content:
            results.append({"document": doc_name, "error": "Could not fetch document"})
            continue
        answer = ask_document_with_claude(title, content, question) if use_ai \
            else ask_document_simple(title, content, question)
        results.append({"document": doc_name, "answer": answer})
    return results


def _query_slack_source(question: str, selected_channels: List[Dict],
                         days_back: int, verbose: bool) -> List[Dict]:
    """Query selected Slack channels and return list of result dicts."""
    results = []
    try:
        querier = SlackQuerier()
        for ch_config in selected_channels:
            ch_name = ch_config["name"]
            if verbose:
                print(f"   Querying: #{ch_name}...")
            keywords = [kw for kw in ch_config.get("keywords", [])
                        if kw.lower() in question.lower()]
            messages = querier.get_channel_messages(
                ch_name, days_back=days_back,
                keywords=keywords if keywords else None
            )
            if messages:
                formatted = f"Found {len(messages)} message(s) in #{ch_name}:\n\n"
                for i, msg in enumerate(messages[:5], 1):
                    formatted += f"{i}. {msg['text'][:200]}\n\n"
            else:
                formatted = f"No recent messages found in #{ch_name}"
            results.append({"channel": ch_name, "messages": messages, "summary": formatted})
    except Exception as e:
        results.append({"error": f"Error querying Slack: {e}"})
    return results


def _extract_sfapi_context(sfapi_result: Dict) -> str:
    """Extract key context from SF API result to enrich a follow-up query.

    Used in chain strategy: pulls system name, date, outage description
    so we can search Slack/Gmail more precisely.
    """
    answer = sfapi_result.get("answer", "")
    # Return the answer text as enriched context — with an LLM this would
    # be parsed more precisely, but even raw it helps Slack keyword search
    return answer.strip()


# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------

def multi_ask(question: str, use_ai: bool = None, verbose: bool = True) -> Dict:
    """Ask a question across Google Docs, Slack, and SF API.

    Source order and strategy are driven by priority_rules in
    documents_config.yaml. Chain-strategy questions (RCA/root cause) query
    SF API first, then use that output to enrich the follow-up query.

    Args:
        question: Natural language question
        use_ai:   Whether to use AI. If None, auto-detect from env
        verbose:  Whether to print progress

    Returns:
        Dict with results from all sources queried
    """
    router = MultiSourceRouter()

    if use_ai is None:
        use_ai = HAS_ANTHROPIC and bool(get_ai_api_key())

    has_slack = HAS_SLACK_SDK and bool(get_slack_token())
    has_sfapi = HAS_SFAPI_MODULE

    if verbose:
        print("=" * 80)
        print("Multi-Source Q&A - Google Docs + Slack + SF API")
        print("=" * 80)
        print()
        print(router.explain_routing(question))
        print()

    all_results = {
        "question": question,
        "sources": {
            "google_docs": {"searched": False, "results": []},
            "slack":        {"searched": False, "results": []},
            "sfapi":        {"searched": False, "results": []},
            "gmail":        {"searched": False, "results": []}
        },
        "mode": "ai" if use_ai else "keyword",
        "routing": {
            "source_order": router.get_source_order(question),
            "is_chain": router.is_chain_question(question)
        }
    }

    source_order = router.get_source_order(question)
    is_chain = router.is_chain_question(question)
    chain_rule = router.get_chain_rule(question) if is_chain else None
    sfapi_context = ""   # used in chain mode to enrich step-2 queries

    days_back = router.strategy.get("slack_days_back", 7)

    # -----------------------------------------------------------------------
    # Execute sources in priority order
    # -----------------------------------------------------------------------
    for source in source_order:

        # ── SF API ──────────────────────────────────────────────────────────
        if source == "sfapi" and has_sfapi:
            all_results["sources"]["sfapi"]["searched"] = True
            result = _query_sfapi_source(question, verbose)
            all_results["sources"]["sfapi"]["results"].append(result)

            # In chain mode: capture SF API output to enrich next query
            if is_chain and "answer" in result:
                sfapi_context = _extract_sfapi_context(result)

                # Optionally stop here if SF API returned nothing useful
                if not sfapi_context:
                    if verbose:
                        print("   ⚠️  SF API returned no outage info — skipping chain step 2\n")
                    break

        # ── Google Docs ─────────────────────────────────────────────────────
        elif source == "google_docs":
            selected_docs = router.select_google_docs(question)
            if not selected_docs:
                continue

            # In chain mode: enrich the question with SF API context
            effective_question = question
            if is_chain and sfapi_context:
                effective_question = f"{question}\n\nContext from SF API:\n{sfapi_context}"
                if verbose:
                    print("   🔗 Chain mode: enriching Google Docs query with SF API context\n")

            if verbose:
                print(f"Searching {len(selected_docs)} Google Doc(s):")
                for doc in selected_docs:
                    print(f"   - {doc['name']}")
                print()

            all_results["sources"]["google_docs"]["searched"] = True
            results = _query_google_docs_source(effective_question, selected_docs, use_ai, verbose)
            all_results["sources"]["google_docs"]["results"].extend(results)
            if verbose:
                print()

        # ── Slack ───────────────────────────────────────────────────────────
        elif source == "slack" and has_slack:
            selected_channels = router.select_slack_channels(question)
            if not selected_channels:
                continue

            # In chain mode: enrich the query sent to Slack
            effective_question = question
            if is_chain and sfapi_context:
                effective_question = f"{question} {sfapi_context}"
                if verbose:
                    print("   🔗 Chain mode: enriching Slack query with SF API context\n")

            if verbose:
                print(f"Searching {len(selected_channels)} Slack channel(s):")
                for ch in selected_channels:
                    print(f"   - #{ch['name']}")
                print()

            all_results["sources"]["slack"]["searched"] = True
            results = _query_slack_source(effective_question, selected_channels, days_back, verbose)
            all_results["sources"]["slack"]["results"].extend(results)
            if verbose:
                print()

        # ── Gmail (placeholder) ─────────────────────────────────────────────
        elif source == "gmail":
            # Not built yet — silently skip
            if verbose:
                print("   📧 Gmail: integration coming soon — skipping\n")
            continue

        elif source == "slack" and not has_slack:
            if verbose:
                print("Slack requested but not available")
                if not HAS_SLACK_SDK:
                    print("   Install: pip install slack-sdk")
                if not get_slack_token():
                    print("   Set: export SLACK_BOT_TOKEN='xoxb-...'")
                print()

    # -----------------------------------------------------------------------
    # Display results
    # -----------------------------------------------------------------------
    if verbose:
        print("=" * 80)
        print("Results:")
        print("=" * 80)
        print()

        for source in source_order:
            if source == "sfapi" and all_results["sources"]["sfapi"]["searched"]:
                print("NERSC SF API:")
                print("-" * 80)
                for result in all_results["sources"]["sfapi"]["results"]:
                    if "error" in result:
                        print(f"   Error: {result['error']}")
                    else:
                        print(f"   {result['answer']}")
                print()

            elif source == "google_docs" and all_results["sources"]["google_docs"]["searched"]:
                print("Google Docs:")
                print("-" * 80)
                for result in all_results["sources"]["google_docs"]["results"]:
                    if "error" in result:
                        print(f"   {result['document']}: {result['error']}")
                    else:
                        print(f"   {result['document']}:")
                        print(f"   {result['answer']}")
                    print()

            elif source == "slack" and all_results["sources"]["slack"]["searched"]:
                print("Slack:")
                print("-" * 80)
                for result in all_results["sources"]["slack"]["results"]:
                    if "error" in result:
                        print(f"   Error: {result['error']}")
                    else:
                        print(f"   #{result['channel']}:")
                        print(f"   {result['summary']}")
                    print()

        print("=" * 80)

    return all_results


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive_mode():
    """Run interactive multi-source Q&A."""
    print()
    print("=" * 80)
    print("Multi-Source Q&A - Interactive Mode")
    print("=" * 80)
    print()
    print("Ask questions and I'll search Google Docs, Slack, and NERSC SF API!")
    print()

    router = MultiSourceRouter()

    print("Available sources:")
    if router.google_docs:
        print(f"   Google Docs: {len(router.google_docs)} document(s)")
        for doc in router.google_docs:
            print(f"      - {doc['name']}")
    if router.slack_channels:
        print(f"   Slack: {len(router.slack_channels)} channel(s)")
        for ch in router.slack_channels:
            print(f"      - #{ch['name']}")
    if HAS_SFAPI_MODULE:
        print(f"   SF API: ✅ Available (NERSC system status, outages)")
    else:
        print(f"   SF API: ❌ Not available (install sfapi_client)")
    print()

    use_ai = HAS_ANTHROPIC and bool(get_ai_api_key())
    if use_ai:
        print("🤖 AI-powered mode enabled")
    else:
        print("🔍 Keyword search mode (set ANTHROPIC_API_KEY or CBORG_API_KEY for AI)")
    print()
    print("Type 'quit' to exit")
    print("=" * 80)
    print()

    while True:
        try:
            question = input("❓ Your question: ").strip()
            if not question:
                continue
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            print()
            multi_ask(question, use_ai=use_ai, verbose=True)
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
Multi-Source Q&A - Search Google Docs, Slack, AND NERSC SF API

USAGE:
  python multi_ask.py "Your question here"    # Single question
  python multi_ask.py                         # Interactive mode

EXAMPLES:
  python multi_ask.py "What is the status of Perlmutter?"
  python multi_ask.py "What were the outages in December?"
  python multi_ask.py "Any planned maintenance?"
  python multi_ask.py "Why did Perlmutter go down last week?"   # chain mode

ROUTING:
  Source order and strategy are controlled by priority_rules in
  documents_config.yaml. Chain-strategy rules (RCA/root cause) query
  SF API first, then use that context to search Slack/Gmail.

CONFIGURATION:
  Edit documents_config.yaml to configure:
  - google_docs, slack_channels, sfapi keywords
  - search_strategy.priority_rules

SETUP:
  1. Configure: documents_config.yaml
  2. Google Docs auth: python test_google_docs.py
  3. Slack token: export SLACK_BOT_TOKEN='xoxb-...'
  4. Ask: python multi_ask.py "question"

OPTIONAL AI MODE:
  export ANTHROPIC_API_KEY='your-key'   # or CBORG_API_KEY
  python multi_ask.py "Summarize all incidents"
            """)
            return

        multi_ask(question, verbose=True)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
