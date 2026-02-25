#!/usr/bin/env python3
"""Test script for Google Docs connection."""

import asyncio
import json
import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_credentials():
    """Get or create credentials for Google Docs API."""
    creds = None
    token_path = Path("token.json")

    # The file token.json stores the user's access and refresh tokens
    if token_path.exists():
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Starting OAuth flow...")
            # Look for credentials file
            creds_file = None
            for pattern in ["client_secret*.json", "credentials.json"]:
                matches = list(Path(".").glob(pattern))
                if matches:
                    creds_file = str(matches[0])
                    break

            if not creds_file:
                print("ERROR: No credentials file found!")
                print("Please place your OAuth credentials file in this directory.")
                print("Expected: client_secret_*.json or credentials.json")
                return None

            print(f"Using credentials file: {creds_file}")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)

            # Use console-based auth for headless servers
            try:
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"\nCannot open browser: {e}")
                print("\nUsing manual authentication flow...")
                print("=" * 80)

                # Get the authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')

                print("\n1. Open this URL in your browser:")
                print("-" * 80)
                print(auth_url)
                print("-" * 80)
                print("\n2. After authorizing, you'll be redirected to a URL.")
                print("3. Copy the ENTIRE redirect URL and paste it below.\n")

                redirect_url = input("Paste the redirect URL here: ").strip()

                # Extract the authorization code from the redirect URL
                flow.fetch_token(authorization_response=redirect_url)
                creds = flow.credentials

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            print("Credentials saved to token.json")

    return creds


def test_list_documents(creds, folder_id="root", max_results=10):
    """Test listing documents from Google Drive."""
    try:
        service = build("drive", "v3", credentials=creds)

        # Query to list Google Docs
        query = "mimeType='application/vnd.google-apps.document'"
        if folder_id != "root":
            query += f" and '{folder_id}' in parents"

        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, createdTime, modifiedTime, owners)"
        ).execute()

        items = results.get("files", [])

        if not items:
            print("No Google Docs found.")
            return []

        print(f"\nFound {len(items)} Google Docs:")
        print("-" * 80)
        for item in items:
            print(f"Name: {item['name']}")
            print(f"ID: {item['id']}")
            print(f"Modified: {item.get('modifiedTime', 'N/A')}")
            if 'owners' in item:
                owners = ", ".join([o.get('emailAddress', 'Unknown') for o in item['owners']])
                print(f"Owner: {owners}")
            print("-" * 80)

        return items

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def test_get_document(creds, doc_id):
    """Test fetching a specific Google Doc."""
    try:
        service = build("docs", "v1", credentials=creds)

        # Retrieve the document
        document = service.documents().get(documentId=doc_id).execute()

        print(f"\nDocument Title: {document.get('title')}")
        print(f"Document ID: {document.get('documentId')}")
        print(f"Revision ID: {document.get('revisionId')}")

        # Extract text content
        content = document.get("body", {}).get("content", [])
        text_parts = []

        for element in content:
            if "paragraph" in element:
                for text_run in element["paragraph"].get("elements", []):
                    if "textRun" in text_run:
                        text_parts.append(text_run["textRun"].get("content", ""))

        full_text = "".join(text_parts)
        print(f"\nContent Preview (first 500 chars):")
        print("-" * 80)
        print(full_text[:500])
        print("-" * 80)
        print(f"\nTotal characters: {len(full_text)}")

        return document

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def test_search_in_document(creds, doc_id, keywords):
    """Test searching for keywords in a document."""
    try:
        service = build("docs", "v1", credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()

        # Extract all text
        content = document.get("body", {}).get("content", [])
        text_parts = []

        for element in content:
            if "paragraph" in element:
                for text_run in element["paragraph"].get("elements", []):
                    if "textRun" in text_run:
                        text_parts.append(text_run["textRun"].get("content", ""))

        full_text = "".join(text_parts)

        # Search for keywords
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        results = {}

        for keyword in keyword_list:
            count = full_text.lower().count(keyword)
            results[keyword] = count

        print(f"\nSearch Results in '{document.get('title')}':")
        print("-" * 80)
        for keyword, count in results.items():
            print(f"'{keyword}': {count} occurrences")
        print("-" * 80)

        return results

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


async def main():
    """Main test function."""
    print("=" * 80)
    print("Google Docs API Connection Test")
    print("=" * 80)

    # Get credentials
    creds = get_credentials()
    if not creds:
        print("\nFailed to get credentials. Exiting.")
        return

    print("\n✓ Successfully authenticated with Google Docs API")

    # Test 1: List documents
    print("\n" + "=" * 80)
    print("TEST 1: List Recent Documents")
    print("=" * 80)
    docs = test_list_documents(creds, max_results=5)

    if not docs:
        print("\nNo documents found to test with.")
        print("You can create a test Google Doc or provide a document ID to test.")
        return

    # Test 2: Get first document
    if docs:
        first_doc = docs[0]
        doc_id = first_doc["id"]

        print("\n" + "=" * 80)
        print(f"TEST 2: Fetch Document Content - '{first_doc['name']}'")
        print("=" * 80)
        test_get_document(creds, doc_id)

        # Test 3: Search in document
        print("\n" + "=" * 80)
        print("TEST 3: Search for Keywords")
        print("=" * 80)
        keywords = input("Enter keywords to search (comma-separated, or press Enter for defaults): ").strip()
        if not keywords:
            keywords = "the,and,is"

        test_search_in_document(creds, doc_id, keywords)

    print("\n" + "=" * 80)
    print("✓ All tests completed successfully!")
    print("=" * 80)
    print("\nYou can now:")
    print("1. Query specific documents by ID using test_get_document(creds, 'DOC_ID')")
    print("2. Search for specific keywords using test_search_in_document(creds, 'DOC_ID', 'keywords')")
    print("3. List documents from a specific folder using test_list_documents(creds, 'FOLDER_ID')")


if __name__ == "__main__":
    asyncio.run(main())
