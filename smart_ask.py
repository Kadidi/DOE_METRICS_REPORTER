#!/usr/bin/env python3
"""Smart Q&A system that automatically finds the right Google Docs to query."""

import sys
import os
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from test_google_docs import get_credentials
from ask_document import get_document_content, ask_document_with_claude, ask_document_simple

# Try to import anthropic
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class DocumentRouter:
    """Routes queries to the most relevant documents."""

    def __init__(self, config_file="documents_config.yaml"):
        """Initialize router with configuration."""
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.documents = self.config.get("documents", [])
        self.strategy = self.config.get("search_strategy", {})

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            print(f"Warning: Config file {self.config_file} not found")
            return {"documents": [], "search_strategy": {"mode": "all", "max_documents": 3}}

        with open(self.config_file) as f:
            return yaml.safe_load(f)

    def select_documents(self, question: str) -> List[Dict]:
        """Select which documents to search based on the question.

        Args:
            question: User's question

        Returns:
            List of document configs to search
        """
        mode = self.strategy.get("mode", "smart")
        max_docs = self.strategy.get("max_documents", 3)

        if mode == "all":
            # Search all documents
            return self.documents[:max_docs]

        elif mode == "first":
            # Just use the first document
            return self.documents[:1] if self.documents else []

        elif mode == "smart":
            # Match keywords in question to document keywords
            question_lower = question.lower()
            scored_docs = []

            for doc in self.documents:
                score = 0
                keywords = doc.get("keywords", [])

                # Count how many document keywords appear in the question
                for keyword in keywords:
                    if keyword.lower() in question_lower:
                        score += 1

                if score > 0:
                    scored_docs.append((score, doc))

            # Sort by score (highest first) and take top N
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            selected = [doc for score, doc in scored_docs[:max_docs]]

            # If no matches, use default category or first document
            if not selected and self.documents:
                default_cat = self.strategy.get("default_category")
                if default_cat:
                    selected = [d for d in self.documents if d.get("category") == default_cat]
                if not selected:
                    selected = [self.documents[0]]

            return selected

        else:
            # Unknown mode, use all
            return self.documents[:max_docs]

    def explain_selection(self, question: str, selected_docs: List[Dict]) -> str:
        """Explain which documents were selected and why."""
        if not selected_docs:
            return "No documents configured to search."

        explanation = f"Searching {len(selected_docs)} document(s):\n"
        for i, doc in enumerate(selected_docs, 1):
            explanation += f"  {i}. {doc['name']} - {doc.get('description', 'No description')}\n"

        return explanation


def smart_ask(question: str, use_ai: bool = None, verbose: bool = True) -> Dict:
    """Ask a question and automatically find the right documents.

    Args:
        question: Natural language question
        use_ai: Whether to use AI (Claude). If None, auto-detect based on API key
        verbose: Whether to print progress

    Returns:
        Dict with results from each document searched
    """
    # Initialize
    router = DocumentRouter()
    creds = get_credentials()

    # Determine if we should use AI
    if use_ai is None:
        use_ai = HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY")

    # Select relevant documents
    selected_docs = router.select_documents(question)

    if not selected_docs:
        return {
            "question": question,
            "error": "No documents configured. Please update documents_config.yaml",
            "results": []
        }

    if verbose:
        print("=" * 80)
        print("Smart Google Docs Q&A")
        print("=" * 80)
        print()
        print(router.explain_selection(question, selected_docs))
        print()
        if use_ai:
            print("🤖 Using AI-powered analysis")
        else:
            print("🔍 Using keyword search")
        print("=" * 80)
        print()

    # Query each selected document
    results = []

    for doc_config in selected_docs:
        doc_id = doc_config["id"]
        doc_name = doc_config["name"]

        if verbose:
            print(f"📄 Searching: {doc_name}")

        # Fetch document
        title, content = get_document_content(creds, doc_id)

        if not content:
            if verbose:
                print(f"   ⚠️  Could not fetch document\n")
            results.append({
                "document": doc_name,
                "document_id": doc_id,
                "error": "Could not fetch document"
            })
            continue

        # Ask question
        if use_ai:
            answer = ask_document_with_claude(title, content, question)
        else:
            answer = ask_document_simple(title, content, question)

        results.append({
            "document": doc_name,
            "document_id": doc_id,
            "title": title,
            "answer": answer,
            "content_length": len(content)
        })

        if verbose:
            print()
            print("💡 Answer:")
            print("-" * 80)
            print(answer)
            print("-" * 80)
            print()

    return {
        "question": question,
        "documents_searched": len(results),
        "results": results,
        "mode": "ai" if use_ai else "keyword"
    }


def interactive_mode():
    """Run interactive Q&A without needing to specify document IDs."""
    print()
    print("=" * 80)
    print("NERSC Google Docs Q&A - Interactive Mode")
    print("=" * 80)
    print()
    print("Just ask your question - I'll find the right documents!")
    print()

    # Check configuration
    router = DocumentRouter()
    if not router.documents:
        print("⚠️  No documents configured!")
        print("Please add documents to: documents_config.yaml")
        print()
        return

    print(f"📚 {len(router.documents)} document(s) available:")
    for doc in router.documents:
        print(f"   • {doc['name']}")
    print()

    # Check if AI is available
    use_ai = HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY")
    if use_ai:
        print("🤖 AI-powered mode enabled")
    else:
        print("🔍 Keyword search mode (set ANTHROPIC_API_KEY for AI)")
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
            smart_ask(question, use_ai=use_ai, verbose=True)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])

        if question in ["--help", "-h", "help"]:
            print("""
Smart Google Docs Q&A - Automatically searches relevant documents

USAGE:
  python smart_ask.py "Your question here"    # Single question
  python smart_ask.py                         # Interactive mode

EXAMPLES:
  python smart_ask.py "What were the outages in December?"
  python smart_ask.py "How many maintenance windows were there?"
  python smart_ask.py "What happened with login nodes?"

CONFIGURATION:
  Edit documents_config.yaml to add/remove documents

FEATURES:
  • Automatically selects relevant documents
  • No need to specify document IDs
  • Searches multiple documents if needed
  • AI-powered analysis (with ANTHROPIC_API_KEY)
  • Falls back to keyword search (free)

SETUP:
  1. Configure documents in documents_config.yaml
  2. Authenticate: python test_google_docs.py
  3. Ask questions: python smart_ask.py "question"

OPTIONAL AI MODE:
  export ANTHROPIC_API_KEY='your-key'
  python smart_ask.py "Summarize all incidents"
            """)
            return

        # Ask single question
        result = smart_ask(question, verbose=True)

        # Exit with status based on whether we got results
        if result.get("error") or not result.get("results"):
            sys.exit(1)

    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
