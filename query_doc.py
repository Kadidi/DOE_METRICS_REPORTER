#!/usr/bin/env python3
"""Quick script to query a specific Google Doc."""

import sys
from test_google_docs import get_credentials, test_get_document, test_search_in_document

if len(sys.argv) < 2:
    print("Usage: python query_doc.py <DOCUMENT_ID> [keywords]")
    print("\nExample:")
    print("  python query_doc.py 1ABC123xyz789")
    print("  python query_doc.py 1ABC123xyz789 'incident,error,failure'")
    sys.exit(1)

doc_id = sys.argv[1]
keywords = sys.argv[2] if len(sys.argv) > 2 else None

print(f"Querying document: {doc_id}")
print("=" * 80)

# Get credentials (uses saved token.json)
creds = get_credentials()

# Fetch document content
print("\nFetching document content...")
test_get_document(creds, doc_id)

# Search for keywords if provided
if keywords:
    print("\nSearching for keywords...")
    test_search_in_document(creds, doc_id, keywords)

print("\n" + "=" * 80)
print("✓ Query completed!")
