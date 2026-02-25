#!/usr/bin/env python3
"""Multi-source Q&A system that queries Google Docs, Slack, AND NERSC SF API automatically."""

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


def get_ai_api_key() -> Optional[str]:
    """Get AI API key from supported environment variables."""
    return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CBORG_API_KEY")


def is_sfapi_question(question: str) -> bool:
    """Determine if a question should be routed to SF API.
    
    Args:
        question: The user's question
        
    Returns:
        True if the question is about NERSC systems/status/outages
    """
    question_lower = question.lower()
    
    # Keywords that indicate SF API should be used
    sfapi_keywords = [
        # System status
        "perlmutter", "nersc", "system status", "systems",
        # Outages
        "outage", "swo", "system wide", "down", "maintenance",
        "planned", "unplanned", "emergency",
        # Queue/jobs
        "queue", "wait time", "jobs",
        # General status
        "status", "running", "available", "degraded", "active"
    ]
    
    for keyword in sfapi_keywords:
        if keyword in question_lower:
            return True
    
    return False


class MultiSourceRouter:
    """Routes queries to Google Docs, Slack, and SF API based on content."""

    def __init__(self, config_file=None):
        """Initialize router with configuration."""
        # Use central config if no file specified
        if config_file is None:
            config_file = get_config_path()

        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.google_docs = self.config.get("google_docs", [])
        self.slack_channels = self.config.get("slack_channels", [])
        self.sfapi_config = self.config.get("sfapi", {"enabled": True})
        self.strategy = self.config.get("search_strategy", {})

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            print(f"Warning: Config file {self.config_file} not found")
            return {
                "google_docs": [],
                "slack_channels": [],
                "sfapi": {"enabled": True},
                "search_strategy": {
                    "sources": ["google_docs", "sfapi"],
                    "mode": "all",
                    "max_per_source": 2
                }
            }

        with open(self.config_file) as f:
            return yaml.safe_load(f)

    def _score_source(self, source: Dict, question: str) -> int:
        """Score how relevant a source is to the question."""
        question_lower = question.lower()
        score = 0
        keywords = source.get("keywords", [])

        for keyword in keywords:
            if keyword.lower() in question_lower:
                score += 1

        return score

    def select_google_docs(self, question: str) -> List[Dict]:
        """Select which Google Docs to search."""
        mode = self.strategy.get("mode", "smart")
        max_docs = self.strategy.get("max_per_source", 2)

        if mode == "all":
            return self.google_docs[:max_docs]
        elif mode == "first":
            return self.google_docs[:1] if self.google_docs else []
        else:  # smart
            scored_docs = [(self._score_source(doc, question), doc) for doc in self.google_docs]
            scored_docs = [(score, doc) for score, doc in scored_docs if score > 0]
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            return [doc for score, doc in scored_docs[:max_docs]]

    def select_slack_channels(self, question: str) -> List[Dict]:
        """Select which Slack channels to search."""
        mode = self.strategy.get("mode", "smart")
        max_channels = self.strategy.get("max_per_source", 2)

        if mode == "all":
            return self.slack_channels[:max_channels]
        elif mode == "first":
            return self.slack_channels[:1] if self.slack_channels else []
        else:  # smart
            scored_channels = [(self._score_source(ch, question), ch) for ch in self.slack_channels]
            scored_channels = [(score, ch) for score, ch in scored_channels if score > 0]
            scored_channels.sort(key=lambda x: x[0], reverse=True)
            return [ch for score, ch in scored_channels[:max_channels]]

    def should_search_source(self, source_name: str) -> bool:
        """Check if we should search a given source."""
        sources = self.strategy.get("sources", ["google_docs"])
        return source_name in sources
    
    def should_search_sfapi(self, question: str) -> bool:
        """Check if we should query SF API for this question."""
        # Check if SF API is enabled in config
        if not self.sfapi_config.get("enabled", True):
            return False
        
        # Check if sfapi is in sources list
        if not self.should_search_source("sfapi"):
            return False
        
        # Check if question is relevant to SF API
        return is_sfapi_question(question)


def multi_ask(question: str, use_ai: bool = None, verbose: bool = True) -> Dict:
    """Ask a question across Google Docs, Slack, and SF API.

    Args:
        question: Natural language question
        use_ai: Whether to use AI (Claude). If None, auto-detect based on API key
        verbose: Whether to print progress

    Returns:
        Dict with results from all sources
    """
    # Initialize
    router = MultiSourceRouter()

    # Determine if we should use AI
    if use_ai is None:
        use_ai = HAS_ANTHROPIC and get_ai_api_key()

    # Check if Slack is available
    has_slack = HAS_SLACK_SDK and get_slack_token()
    
    # Check if SF API is available
    has_sfapi = HAS_SFAPI_MODULE

    if verbose:
        print("=" * 80)
        print("Multi-Source Q&A - Google Docs + Slack + SF API")
        print("=" * 80)
        print()

    all_results = {
        "question": question,
        "sources": {
            "google_docs": {"searched": False, "results": []},
            "slack": {"searched": False, "results": []},
            "sfapi": {"searched": False, "results": []}
        },
        "mode": "ai" if use_ai else "keyword"
    }

    # ==========================================================================
    # Query SF API (for NERSC system status, outages, etc.)
    # ==========================================================================
    if has_sfapi and router.should_search_sfapi(question):
        if verbose:
            print("Querying NERSC Superfacility API...")
            print()
        
        all_results["sources"]["sfapi"]["searched"] = True
        
        try:
            sfapi_result = query_sfapi(question)
            all_results["sources"]["sfapi"]["results"].append({
                "source": "sfapi",
                "answer": sfapi_result.get("answer", "No answer"),
                "raw": sfapi_result.get("raw", {})
            })
            
            if verbose:
                print(f"   ✅ SF API query complete")
                print()
                
        except Exception as e:
            all_results["sources"]["sfapi"]["results"].append({
                "source": "sfapi",
                "error": str(e)
            })
            if verbose:
                print(f"   ❌ SF API error: {e}")
                print()

    # ==========================================================================
    # Query Google Docs
    # ==========================================================================
    if router.should_search_source("google_docs"):
        selected_docs = router.select_google_docs(question)

        if selected_docs:
            if verbose:
                print(f"Searching {len(selected_docs)} Google Doc(s):")
                for doc in selected_docs:
                    print(f"   - {doc['name']}")
                print()

            all_results["sources"]["google_docs"]["searched"] = True
            if not HAS_GOOGLE_DOCS:
                all_results["sources"]["google_docs"]["results"].append({
                    "document": "Google Docs",
                    "error": "Google Docs dependencies not installed"
                })
                selected_docs = []
            else:
                creds = get_credentials()

            for doc_config in selected_docs:
                doc_id = doc_config["id"]
                doc_name = doc_config["name"]

                if verbose:
                    print(f"   Querying: {doc_name}...")

                # Fetch document
                title, content = get_document_content(creds, doc_id)

                if not content:
                    all_results["sources"]["google_docs"]["results"].append({
                        "document": doc_name,
                        "error": "Could not fetch document"
                    })
                    continue

                # Ask question
                if use_ai:
                    answer = ask_document_with_claude(title, content, question)
                else:
                    answer = ask_document_simple(title, content, question)

                all_results["sources"]["google_docs"]["results"].append({
                    "document": doc_name,
                    "answer": answer
                })

            if verbose:
                print()

    # ==========================================================================
    # Query Slack
    # ==========================================================================
    if router.should_search_source("slack") and has_slack:
        selected_channels = router.select_slack_channels(question)

        if selected_channels:
            if verbose:
                print(f"Searching {len(selected_channels)} Slack channel(s):")
                for ch in selected_channels:
                    print(f"   - #{ch['name']}")
                print()

            all_results["sources"]["slack"]["searched"] = True
            days_back = router.strategy.get("slack_days_back", 7)

            try:
                querier = SlackQuerier()

                for ch_config in selected_channels:
                    ch_name = ch_config["name"]

                    if verbose:
                        print(f"   Querying: #{ch_name}...")

                    # Extract keywords from question for Slack search
                    keywords = [kw for kw in ch_config.get("keywords", [])
                               if kw.lower() in question.lower()]

                    messages = querier.get_channel_messages(
                        ch_name,
                        days_back=days_back,
                        keywords=keywords if keywords else None
                    )

                    if messages:
                        formatted_msgs = f"Found {len(messages)} message(s) in #{ch_name}:\n\n"
                        for i, msg in enumerate(messages[:5], 1):  # Show top 5
                            formatted_msgs += f"{i}. {msg['text'][:200]}\n\n"
                    else:
                        formatted_msgs = f"No recent messages found in #{ch_name}"

                    all_results["sources"]["slack"]["results"].append({
                        "channel": ch_name,
                        "messages": messages,
                        "summary": formatted_msgs
                    })

            except Exception as e:
                all_results["sources"]["slack"]["results"].append({
                    "error": f"Error querying Slack: {e}"
                })

            if verbose:
                print()

    elif router.should_search_source("slack") and not has_slack:
        if verbose:
            print("Slack search requested but not available")
            if not HAS_SLACK_SDK:
                print("   Install: pip install slack-sdk")
            if not os.getenv("SLACK_BOT_TOKEN"):
                print("   Set: export SLACK_BOT_TOKEN='xoxb-...'")
            print()

    # ==========================================================================
    # Display results
    # ==========================================================================
    if verbose:
        print("=" * 80)
        print("Results:")
        print("=" * 80)
        print()

        # SF API results (show first since they're usually most relevant for status)
        if all_results["sources"]["sfapi"]["searched"]:
            print("NERSC SF API:")
            print("-" * 80)
            for result in all_results["sources"]["sfapi"]["results"]:
                if "error" in result:
                    print(f"   Error: {result['error']}")
                else:
                    print(f"   {result['answer']}")
            print()

        # Google Docs results
        if all_results["sources"]["google_docs"]["searched"]:
            print("Google Docs:")
            print("-" * 80)
            for result in all_results["sources"]["google_docs"]["results"]:
                if "error" in result:
                    print(f"   {result['document']}: {result['error']}")
                else:
                    print(f"   {result['document']}:")
                    print(f"   {result['answer']}")
                print()

        # Slack results
        if all_results["sources"]["slack"]["searched"]:
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


def interactive_mode():
    """Run interactive multi-source Q&A."""
    print()
    print("=" * 80)
    print("Multi-Source Q&A - Interactive Mode")
    print("=" * 80)
    print()
    print("Ask questions and I'll search Google Docs, Slack, and NERSC SF API!")
    print()

    # Check configuration
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

    # Check AI availability
    use_ai = HAS_ANTHROPIC and get_ai_api_key()
    if use_ai:
        print("AI-powered mode enabled")
    else:
        print("Keyword search mode (set ANTHROPIC_API_KEY or CBORG_API_KEY for AI)")
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


def main():
    """Main entry point."""
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
  python multi_ask.py "What was the last SWO?"

CONFIGURATION:
  Edit documents_config.yaml to configure:
  - Which Google Docs to search
  - Which Slack channels to search
  - SF API settings
  - Search strategy (smart, all, first)

FEATURES:
  • Searches Google Docs, Slack, AND SF API automatically
  • Smart routing based on keywords
  • NERSC system status and outage information
  • Combines results from all sources

SETUP:
  1. Configure: documents_config.yaml
  2. Google Docs auth: python test_google_docs.py
  3. Slack token: export SLACK_BOT_TOKEN='xoxb-...'
  4. SF API: export SFAPI_CLIENT_ID='...'
  5. Ask: python multi_ask.py "question"

OPTIONAL AI MODE:
  export ANTHROPIC_API_KEY='your-key'
  python multi_ask.py "Summarize all incidents"
            """)
            return

        # Ask single question
        result = multi_ask(question, verbose=True)

    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
