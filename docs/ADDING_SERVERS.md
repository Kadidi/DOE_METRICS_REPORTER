# Adding New MCP Servers Guide

Step-by-step guide to extend DOE_METRICS_REPORTER with new data sources (e.g., ServiceNow, Gmail, IRIS).

## Architecture Overview

Each MCP server is a standalone Python module that:
1. Implements data-specific tools (search, list, fetch operations)
2. Manages external API calls
3. Returns results as JSON
4. Is discovered and loaded dynamically by the CLI client

## Creating a New Server

### Step 1: Copy Server Template

```bash
cp servers/server_template.py servers/my_new_api_server.py
```

### Step 2: Implement Server Class

Edit `servers/my_new_api_server.py`:

```python
"""MCP server for MyAPI integration."""

import json
import logging
import os
from fastmcp import Server

logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("my_new_api_server")  # Update name


@server.list_tools()
def list_tools() -> list:
    """List available tools for this API."""
    return [
        {
            "name": "search_resources",
            "description": "Search for resources in MyAPI",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default: 10)"
                    }
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_resource",
            "description": "Get details of a specific resource",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "Resource ID"
                    }
                },
                "required": ["resource_id"],
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name."""
    try:
        if name == "search_resources":
            query = arguments["query"]
            limit = arguments.get("limit", 10)
            return await search_resources(query, limit)
        elif name == "get_resource":
            resource_id = arguments["resource_id"]
            return await get_resource(resource_id)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return json.dumps({"error": str(e)})


async def search_resources(query: str, limit: int = 10) -> str:
    """Search for resources in MyAPI.

    Args:
        query: Search query
        limit: Max results to return

    Returns:
        JSON with search results
    """
    try:
        # 1. Check if we should use cache
        # from cache import CacheManager
        # cache = CacheManager()
        # cached = cache.get("myapi", query)
        # if cached:
        #     return json.dumps({**cached["data"], "cache_hit": True})

        # 2. Call external API
        api_key = os.getenv("MYAPI_API_KEY", "")
        # results = await _call_myapi(api_key, query, limit)

        # 3. Cache results
        # cache.set("myapi", query, results, ttl_hours=6)

        results = {
            "query": query,
            "results": [],
            "count": 0,
            "cached_at": None,
            "cache_hit": False,
        }

        return json.dumps(results)
    except Exception as e:
        logger.error(f"Error searching MyAPI: {e}")
        return json.dumps({"error": str(e)})


async def get_resource(resource_id: str) -> str:
    """Get details of a specific resource.

    Args:
        resource_id: The resource ID

    Returns:
        JSON with resource details
    """
    result = {
        "resource_id": resource_id,
        "data": {},
        "cached_at": None,
        "cache_hit": False,
    }
    return json.dumps(result)


if __name__ == "__main__":
    # For testing the server standalone
    import asyncio

    async def test():
        result = await call_tool("search_resources", {"query": "test"})
        print(result)

    asyncio.run(test())
```

### Step 3: Add Server to Registry

Edit `servers.config` to register your new server:

```
# Existing servers
google_docs:servers/google_docs_server.py
slack:servers/slack_server.py

# New server
myapi:servers/my_new_api_server.py
```

### Step 4: Test the Server

#### Test Standalone

```bash
python3 servers/my_new_api_server.py
```

#### Test with CLI

```bash
./start_reporter.sh
```

You should see:
```
✓ Found server: myapi (servers/my_new_api_server.py)
```

In the CLI:
```bash
DOE_METRICS> servers list
Loaded servers (3):
  ✓ google_docs
  ✓ myapi
  ✓ slack
```

## Example: ServiceNow Integration

Here's how to implement a ServiceNow server:

```python
"""MCP server for ServiceNow incident queries."""

import json
import logging
import os
import httpx
from fastmcp import Server

logger = logging.getLogger(__name__)
server = Server("servicenow_server")


@server.list_tools()
def list_tools() -> list:
    return [
        {
            "name": "search_incidents",
            "description": "Search ServiceNow incidents",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string"},
                    "state": {
                        "type": "string",
                        "enum": ["new", "in_progress", "resolved", "all"]
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "all"]
                    }
                },
                "required": ["keywords"],
            },
        },
        {
            "name": "get_incident",
            "description": "Get details of specific incident",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"}
                },
                "required": ["incident_id"],
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    try:
        if name == "search_incidents":
            return await search_incidents(
                arguments["keywords"],
                arguments.get("state", "all"),
                arguments.get("priority", "all")
            )
        elif name == "get_incident":
            return await get_incident(arguments["incident_id"])
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps({"error": str(e)})


async def search_incidents(keywords: str, state: str, priority: str) -> str:
    """Search ServiceNow incidents."""
    instance = os.getenv("SERVICENOW_INSTANCE")
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")

    # Build query
    query_parts = [f"short_descriptionLIKE{keywords}"]
    if state != "all":
        query_parts.append(f"state={state}")
    if priority != "all":
        query_parts.append(f"priority={priority}")

    query = "^".join(query_parts)
    url = f"https://{instance}/api/now/table/incident?sysparm_query={query}"

    async with httpx.AsyncClient(auth=(username, password)) as client:
        response = await client.get(url)
        data = response.json()

    return json.dumps({
        "query": keywords,
        "incidents": data.get("result", []),
        "count": len(data.get("result", [])),
        "cached_at": None,
        "cache_hit": False,
    })


async def get_incident(incident_id: str) -> str:
    """Get specific incident details."""
    # Similar implementation...
    return json.dumps({"incident_id": incident_id})
```

## Best Practices

### 1. Error Handling

Always wrap API calls in try-except:

```python
try:
    result = await api.search(query)
except Exception as e:
    logger.error(f"API error: {e}")
    return json.dumps({"error": str(e), "api": "myapi"})
```

### 2. Caching

Use CacheManager for frequently-accessed data:

```python
from cache import CacheManager

cache = CacheManager()

# Check cache first
cached = cache.get("myapi", query)
if cached:
    return json.dumps({**cached["data"], "cache_hit": True})

# Fetch from API
results = await fetch_from_api(query)

# Cache results (6 hours)
cache.set("myapi", query, results, ttl_hours=6)

return json.dumps(results)
```

### 3. Type Hints

Use Python type hints for clarity:

```python
async def search_resources(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, str]] = None
) -> str:
    """Search for resources."""
    ...
```

### 4. Logging

Log important events:

```python
logger.info(f"Searching {api} for '{query}'")
logger.debug(f"API response: {response}")
logger.warning(f"Rate limit approaching: {remaining}/hour")
logger.error(f"API error: {error}")
```

### 5. Data Models

Use Pydantic models for consistency:

```python
from models import BaseModel
from typing import List

class ServiceNowIncident(BaseModel):
    number: str
    short_description: str
    state: str
    priority: str
    created_at: datetime
    updated_at: datetime
```

### 6. Tool Schema

Design tools with clear, specific purposes:

```python
# Good: Specific, limited scope
{
    "name": "search_open_incidents",
    "description": "Search open ServiceNow incidents",
    "inputSchema": {
        "properties": {
            "keywords": {"type": "string"},
            "priority": {"type": "string", "enum": ["critical", "high"]}
        }
    }
}

# Less good: Vague, broad scope
{
    "name": "servicenow_query",
    "description": "Query ServiceNow",
    "inputSchema": {...}
}
```

## Disabling Servers

To temporarily disable a server without deleting it:

```bash
# Edit servers.config
# Comment out the line:
# myapi:servers/my_new_api_server.py

# Save and restart
./start_reporter.sh
```

## Debugging

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG

# Or in code
logging.basicConfig(level=logging.DEBUG)
```

### Test API Connectivity

```python
# Create a simple test script
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/health")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.json()}")
```

### Verify Server Loading

```bash
DOE_METRICS> servers list
```

If your server doesn't appear, check:
1. Server file exists and is readable
2. Server name in servers.config matches
3. Server Python syntax is valid
4. No import errors (check logs)

## Example Implementations

See `servers/` directory for complete implementations:
- `google_docs_server.py` - Document API integration
- `slack_server.py` - Chat API integration
- `server_template.py` - Template for new servers

## Phase 2 & 3 Roadmap

When ready to implement Phase 2 servers, copy the patterns shown here:

**Phase 2:**
- `elasticsearch_server.py` - System metrics queries
- `slurm_server.py` - Job analysis via sacct

**Phase 3:**
- `servicenow_server.py` - Incident management
- `gmail_server.py` - Email queries
- `iris_server.py` - Job metadata

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'cache'"

Ensure you're in the DOE_METRICS_REPORTER directory and installed the package:
```bash
cd DOE_METRICS_REPORTER
pip install -e .
```

### "ImportError: cannot import name 'fastmcp'"

Install missing dependency:
```bash
pip install fastmcp
```

### Server loads but tools don't work

Check:
1. Tool method is decorated with `@server.call_tool()`
2. Tool name in `list_tools()` matches `call_tool()` handler
3. Input schema matches actual parameters
4. No unhandled exceptions in tool methods

### Async/await issues

Ensure all I/O operations use `async`:
```python
# Good
async def search(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Bad (blocking)
def search(query: str):
    response = requests.get(url)  # Blocks entire client!
    return response.json()
```

---

**Last Updated:** 2025-01-26
