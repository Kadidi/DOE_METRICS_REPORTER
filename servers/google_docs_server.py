"""MCP server for querying Google Docs (Phase 1 MVP)."""

import json
import logging
import os
from typing import Optional
from fastmcp import Server

logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("google_docs_server")


def _get_auth_headers() -> dict:
    """Get Google API authentication headers."""
    # In production, use OAuth flow with google-auth-oauthlib
    # For now, return placeholder
    api_key = os.getenv("GOOGLE_DOCS_API_KEY", "")
    return {"Authorization": f"Bearer {api_key}"}


@server.list_tools()
def list_tools() -> list:
    """List available Google Docs tools."""
    return [
        {
            "name": "list_documents",
            "description": "List accessible Google Docs in a folder",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Google Drive folder ID (optional, uses root if omitted)",
                    },
                },
                "required": [],
            },
        },
        {
            "name": "get_document_content",
            "description": "Fetch full content of a Google Doc",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "Google Doc ID",
                    },
                },
                "required": ["doc_id"],
            },
        },
        {
            "name": "search_document",
            "description": "Search for keywords within a Google Doc",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "Google Doc ID",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search for (comma-separated)",
                    },
                },
                "required": ["doc_id", "keywords"],
            },
        },
        {
            "name": "list_shared_documents",
            "description": "List documents shared with you",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional search query (e.g., incident, maintenance)",
                    },
                },
                "required": [],
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute a Google Docs tool."""
    try:
        if name == "list_documents":
            folder_id = arguments.get("folder_id", "root")
            return await list_documents(folder_id)
        elif name == "get_document_content":
            doc_id = arguments["doc_id"]
            return await get_document_content(doc_id)
        elif name == "search_document":
            doc_id = arguments["doc_id"]
            keywords = arguments["keywords"]
            return await search_document(doc_id, keywords)
        elif name == "list_shared_documents":
            query = arguments.get("query", "")
            return await list_shared_documents(query)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return json.dumps({"error": str(e)})


async def list_documents(folder_id: str = "root") -> str:
    """List Google Docs in a folder.

    Args:
        folder_id: Google Drive folder ID

    Returns:
        JSON with document list
    """
    # Placeholder implementation
    # In production: Use google-api-python-client with google.auth
    result = {
        "folder_id": folder_id,
        "documents": [
            {
                "id": "doc_001",
                "name": "NERSC Incident Log",
                "created": "2025-01-15",
                "modified": "2025-01-26",
            },
            {
                "id": "doc_002",
                "name": "Maintenance Schedule 2025",
                "created": "2025-01-01",
                "modified": "2025-01-20",
            },
        ],
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


async def get_document_content(doc_id: str) -> str:
    """Fetch full Google Doc content.

    Args:
        doc_id: Google Doc ID

    Returns:
        JSON with document content and metadata
    """
    # Placeholder implementation
    result = {
        "doc_id": doc_id,
        "title": "Example Document",
        "content": "Document content would be fetched from Google Docs API",
        "word_count": 1500,
        "created": "2025-01-15T10:30:00Z",
        "modified": "2025-01-26T14:00:00Z",
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


async def search_document(doc_id: str, keywords: str) -> str:
    """Search for keywords in a Google Doc.

    Args:
        doc_id: Google Doc ID
        keywords: Comma-separated keywords

    Returns:
        JSON with search results
    """
    # Placeholder implementation
    keyword_list = [k.strip() for k in keywords.split(",")]
    result = {
        "doc_id": doc_id,
        "keywords": keyword_list,
        "matches": [
            {
                "keyword": "incident",
                "occurrences": 5,
                "snippets": [
                    "...reported incident at 10:30 AM...",
                    "...incident was resolved by...",
                ],
            },
        ],
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


async def list_shared_documents(query: str = "") -> str:
    """List documents shared with current user.

    Args:
        query: Optional search query

    Returns:
        JSON with shared documents
    """
    # Placeholder implementation
    result = {
        "query": query,
        "documents": [
            {
                "id": "shared_doc_001",
                "name": "Perlmutter Incidents - Jan 2025",
                "owner": "system-admin@nersc.gov",
                "shared_date": "2025-01-20",
            },
        ],
        "count": 1,
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


if __name__ == "__main__":
    # For testing the server standalone
    import asyncio

    async def test():
        """Test the server with sample tool calls."""
        result1 = await call_tool("list_documents", {})
        print("list_documents:", result1)

        result2 = await call_tool("get_document_content", {"doc_id": "doc_001"})
        print("get_document_content:", result2)

        result3 = await call_tool(
            "search_document", {"doc_id": "doc_001", "keywords": "incident"}
        )
        print("search_document:", result3)

    asyncio.run(test())
