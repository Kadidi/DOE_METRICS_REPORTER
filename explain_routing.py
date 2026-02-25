#!/usr/bin/env python3
"""Explain how the routing algorithm selects sources for a given question."""

import sys
from multi_ask import MultiSourceRouter

def explain_routing(question: str):
    """Show which sources would be selected and why."""
    router = MultiSourceRouter()

    print("=" * 80)
    print(f"Question: \"{question}\"")
    print("=" * 80)
    print()

    # Analyze Google Docs
    print("📄 GOOGLE DOCS SCORING:")
    print("-" * 80)
    for doc in router.google_docs:
        score = router._score_source(doc, question)
        print(f"  {doc['name']:<40} Score: {score}")
        if score > 0:
            matches = [kw for kw in doc['keywords'] if kw.lower() in question.lower()]
            print(f"    Matched keywords: {', '.join(matches)}")
        print()

    selected_docs = router.select_google_docs(question)
    print(f"  ✓ Selected: {len(selected_docs)} document(s)")
    for doc in selected_docs:
        print(f"    • {doc['name']}")
    print()

    # Analyze Slack
    print("💬 SLACK CHANNELS SCORING:")
    print("-" * 80)
    for ch in router.slack_channels:
        score = router._score_source(ch, question)
        print(f"  #{ch['name']:<40} Score: {score}")
        if score > 0:
            matches = [kw for kw in ch['keywords'] if kw.lower() in question.lower()]
            print(f"    Matched keywords: {', '.join(matches)}")
        print()

    selected_channels = router.select_slack_channels(question)
    print(f"  ✓ Selected: {len(selected_channels)} channel(s)")
    for ch in selected_channels:
        print(f"    • #{ch['name']}")
    print()

    print("=" * 80)
    print("SUMMARY:")
    print(f"  Total sources to search: {len(selected_docs) + len(selected_channels)}")
    print(f"    Google Docs: {len(selected_docs)}")
    print(f"    Slack: {len(selected_channels)}")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python explain_routing.py \"Your question\"")
        print()
        print("Examples:")
        print('  python explain_routing.py "What outages happened?"')
        print('  python explain_routing.py "What events are coming up?"')
        print('  python explain_routing.py "Perlmutter performance issues"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    explain_routing(question)
