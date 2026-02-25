#!/usr/bin/env python3
"""Quick script to list your Google Docs."""

import sys
from test_google_docs import get_credentials, test_list_documents

# Get number of docs to list from command line, default to 10
max_results = int(sys.argv[1]) if len(sys.argv) > 1 else 10

print(f"Listing up to {max_results} Google Docs...")
print("=" * 80)

# Get credentials (uses saved token.json)
creds = get_credentials()

# List documents
docs = test_list_documents(creds, max_results=max_results)

if docs:
    print(f"\n✓ Found {len(docs)} documents")
    print("\nTo query a specific document, use:")
    print(f"  python query_doc.py <DOCUMENT_ID>")
    print(f"\nExample:")
    if docs:
        print(f"  python query_doc.py {docs[0]['id']}")
else:
    print("\nNo documents found.")
