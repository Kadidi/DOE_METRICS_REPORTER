#!/usr/bin/env python3
"""Natural language Q&A system for Google Docs using Claude API."""

import sys
import os
from test_google_docs import get_credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Try to import anthropic, fallback to basic response if not available
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: anthropic package not installed. Install with: pip install anthropic")


def get_document_content(creds, doc_id):
    """Fetch the full text content of a Google Doc.

    Args:
        creds: Google API credentials
        doc_id: Google Doc ID

    Returns:
        Tuple of (title, content) or (None, None) if error
    """
    try:
        service = build("docs", "v1", credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()

        title = document.get('title', 'Untitled')

        # Extract all text content
        content = document.get("body", {}).get("content", [])
        text_parts = []

        for element in content:
            if "paragraph" in element:
                for text_run in element["paragraph"].get("elements", []):
                    if "textRun" in text_run:
                        text_parts.append(text_run["textRun"].get("content", ""))

        full_text = "".join(text_parts)
        return title, full_text

    except HttpError as error:
        print(f"Error fetching document: {error}")
        return None, None


def ask_document_with_claude(document_title, document_content, question, api_key=None):
    """Use Claude API to answer questions about the document.

    Args:
        document_title: Title of the document
        document_content: Full text content
        question: Natural language question
        api_key: Anthropic-compatible API key (optional, reads from
                 ANTHROPIC_API_KEY or CBORG_API_KEY env var)

    Returns:
        Answer string
    """
    if not HAS_ANTHROPIC:
        return "Error: anthropic package not installed. Run: pip install anthropic"

    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CBORG_API_KEY")

    if not api_key:
        return (
            "Error: AI API key not set. Please set it in your environment:\n"
            "export ANTHROPIC_API_KEY='your-api-key-here'\n"
            "or export CBORG_API_KEY='your-api-key-here'"
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Create the prompt
    prompt = f"""You are a helpful assistant that answers questions about documents.

Document Title: {document_title}

Document Content:
{document_content}

User Question: {question}

Please provide a clear, concise answer based on the document content above. If the information is not in the document, say so clearly. Include specific details from the document when relevant (dates, numbers, systems, etc.)."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        return f"Error calling Claude API: {e}"


def ask_document_simple(document_title, document_content, question):
    """Simple keyword-based search fallback (no LLM required).

    Args:
        document_title: Title of the document
        document_content: Full text content
        question: Natural language question

    Returns:
        Answer string with relevant excerpts
    """
    # Extract keywords from question (simple approach)
    keywords = question.lower().replace("?", "").split()
    # Filter out common words
    stop_words = {"what", "when", "where", "who", "how", "is", "are", "was", "were",
                  "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or"}
    keywords = [k for k in keywords if k not in stop_words]

    # Find relevant lines
    lines = document_content.split('\n')
    relevant_lines = []

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            relevant_lines.append(line.strip())

    if relevant_lines:
        answer = f"Based on '{document_title}', here are the relevant excerpts:\n\n"
        answer += "\n".join(f"- {line}" for line in relevant_lines[:10])  # Limit to 10 lines
        if len(relevant_lines) > 10:
            answer += f"\n\n(... and {len(relevant_lines) - 10} more matches)"
        return answer
    else:
        return f"No relevant information found in '{document_title}' for your question."


def main():
    """Main entry point for interactive Q&A."""
    if len(sys.argv) < 2:
        print("Usage: python ask_document.py <DOCUMENT_ID> [question]")
        print("\nExamples:")
        print("  # Interactive mode:")
        print("  python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8")
        print()
        print("  # Single question:")
        print("  python ask_document.py 1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8 'What were the unplanned outages?'")
        print()
        print("Setup:")
        print("  export ANTHROPIC_API_KEY='your-key-here'  # For Claude API (recommended)")
        print("  # OR use simple keyword search (no API key needed)")
        sys.exit(1)

    doc_id = sys.argv[1]
    single_question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

    print("=" * 80)
    print("Natural Language Q&A for Google Docs")
    print("=" * 80)

    # Get credentials and fetch document
    print("\n📄 Fetching document...")
    creds = get_credentials()
    title, content = get_document_content(creds, doc_id)

    if not content:
        print("❌ Failed to fetch document")
        sys.exit(1)

    print(f"✓ Loaded: {title}")
    print(f"✓ Content: {len(content)} characters\n")

    # Check if we have Claude API
    use_claude = HAS_ANTHROPIC and (os.getenv("ANTHROPIC_API_KEY") or os.getenv("CBORG_API_KEY"))
    if use_claude:
        print("🤖 Using Claude API for intelligent answers")
    else:
        print("🔍 Using simple keyword search (set ANTHROPIC_API_KEY or CBORG_API_KEY for better results)")

    print("=" * 80)

    # Handle single question or interactive mode
    if single_question:
        # Single question mode
        print(f"\n❓ Question: {single_question}\n")

        if use_claude:
            answer = ask_document_with_claude(title, content, single_question)
        else:
            answer = ask_document_simple(title, content, single_question)

        print("💡 Answer:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
    else:
        # Interactive mode
        print("\n💬 Interactive Q&A Mode")
        print("Type your questions (or 'quit' to exit)\n")

        while True:
            try:
                question = input("❓ Your question: ").strip()

                if not question:
                    continue

                if question.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                print()

                if use_claude:
                    answer = ask_document_with_claude(title, content, question)
                else:
                    answer = ask_document_simple(title, content, question)

                print("💡 Answer:")
                print("-" * 80)
                print(answer)
                print("-" * 80)
                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
