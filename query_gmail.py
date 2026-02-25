#!/usr/bin/env python3
"""Gmail integration for querying emails with filters."""

import os
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.mime.text import MIMEText

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2.credentials import Credentials
    HAS_GMAIL_API = True
except ImportError:
    HAS_GMAIL_API = False

# Import central config
try:
    from config import get_google_token_path
except ImportError:
    def get_google_token_path():
        """Fallback if config.py not available."""
        return os.path.expanduser("~/token.json")


class GmailQuerier:
    """Query Gmail with filters."""

    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Gmail client.

        Args:
            credentials_path: Path to credentials JSON file (uses token.json if not provided)
        """
        if not HAS_GMAIL_API:
            raise ImportError("Google API client not installed. Run: pip install google-api-python-client")

        # Use existing Google credentials from Google Docs auth
        self.creds_path = credentials_path or get_google_token_path()

        if not os.path.exists(self.creds_path):
            raise ValueError(
                f"Gmail credentials not found at {self.creds_path}\n"
                "Run: python test_google_docs.py (to authenticate with Google)"
            )

        # Load credentials
        self.creds = Credentials.from_authorized_user_file(self.creds_path)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def search_emails(
        self,
        query: str,
        max_results: int = 10,
        include_body: bool = True
    ) -> List[Dict]:
        """Search emails using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "from:user@example.com subject:incident")
            max_results: Maximum number of emails to return
            include_body: Whether to fetch full email body

        Returns:
            List of email dicts with metadata and content

        Gmail Query Examples:
            - "from:alerts@example.com" - Emails from specific sender
            - "subject:incident" - Emails with "incident" in subject
            - "after:2024/01/01" - Emails after date
            - "has:attachment" - Emails with attachments
            - "is:unread" - Unread emails
            - "label:important" - Emails with label
            - "from:user@example.com subject:outage" - Combined filters
        """
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return []

            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'], include_body)
                if email_data:
                    emails.append(email_data)

            return emails

        except HttpError as error:
            print(f"Gmail API error: {error}")
            return []

    def _get_email_details(self, msg_id: str, include_body: bool = True) -> Optional[Dict]:
        """Get detailed information for a single email.

        Args:
            msg_id: Gmail message ID
            include_body: Whether to fetch body content

        Returns:
            Dict with email details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full' if include_body else 'metadata'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            # Extract body
            body = ""
            if include_body:
                body = self._extract_body(message['payload'])

            # Parse date
            date_str = headers.get('Date', '')

            email_data = {
                'id': msg_id,
                'thread_id': message.get('threadId'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'date': date_str,
                'snippet': message.get('snippet', ''),
                'body': body,
                'labels': message.get('labelIds', []),
            }

            return email_data

        except HttpError as error:
            print(f"Error fetching email {msg_id}: {error}")
            return None

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body text
        """
        body = ""

        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            # Simple message
            if 'data' in payload.get('body', {}):
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        return body

    def search_by_filter(
        self,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        has_attachment: bool = False,
        is_unread: bool = False,
        label: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict]:
        """Search emails using structured filters.

        Args:
            sender: Email address of sender (e.g., "alerts@example.com")
            subject: Keywords in subject line
            after_date: Date string in YYYY/MM/DD format
            before_date: Date string in YYYY/MM/DD format
            has_attachment: Only emails with attachments
            is_unread: Only unread emails
            label: Gmail label name
            max_results: Maximum results to return

        Returns:
            List of email dicts
        """
        # Build query
        query_parts = []

        if sender:
            query_parts.append(f"from:{sender}")
        if subject:
            query_parts.append(f"subject:{subject}")
        if after_date:
            query_parts.append(f"after:{after_date}")
        if before_date:
            query_parts.append(f"before:{before_date}")
        if has_attachment:
            query_parts.append("has:attachment")
        if is_unread:
            query_parts.append("is:unread")
        if label:
            query_parts.append(f"label:{label}")

        query = " ".join(query_parts)

        return self.search_emails(query, max_results=max_results)

    def get_recent_emails(self, days_back: int = 7, max_results: int = 10) -> List[Dict]:
        """Get recent emails from the last N days.

        Args:
            days_back: Number of days to look back
            max_results: Maximum emails to return

        Returns:
            List of email dicts
        """
        # Calculate date
        date = datetime.now() - timedelta(days=days_back)
        after_date = date.strftime("%Y/%m/%d")

        return self.search_by_filter(after_date=after_date, max_results=max_results)


def format_emails_for_display(emails: List[Dict]) -> str:
    """Format emails for display in multi_ask results.

    Args:
        emails: List of email dicts

    Returns:
        Formatted string
    """
    if not emails:
        return "No emails found matching the criteria."

    result = f"Found {len(emails)} email(s):\n\n"

    for i, email in enumerate(emails, 1):
        result += f"{i}. From: {email['from']}\n"
        result += f"   Subject: {email['subject']}\n"
        result += f"   Date: {email['date']}\n"
        result += f"   Preview: {email['snippet'][:150]}...\n"
        result += "\n"

    return result


if __name__ == "__main__":
    # Test Gmail integration
    import sys

    if not HAS_GMAIL_API:
        print("Error: Google API client not installed")
        print("Run: pip install google-api-python-client google-auth-oauthlib")
        sys.exit(1)

    try:
        querier = GmailQuerier()
        print("✓ Gmail authentication successful!")
        print()

        # Test: Get recent emails
        print("Test: Recent emails (last 7 days)")
        print("=" * 80)

        if len(sys.argv) > 1:
            # Use command line query
            query = " ".join(sys.argv[1:])
            print(f"Query: {query}")
            print()
            emails = querier.search_emails(query, max_results=5)
        else:
            # Default: recent emails
            emails = querier.get_recent_emails(days_back=7, max_results=5)

        if emails:
            for i, email in enumerate(emails, 1):
                print(f"{i}. From: {email['from']}")
                print(f"   Subject: {email['subject']}")
                print(f"   Date: {email['date']}")
                print(f"   Snippet: {email['snippet'][:100]}...")
                print()
        else:
            print("No emails found")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
