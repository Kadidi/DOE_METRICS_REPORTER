# DOE_METRICS_REPORTER - Architecture Documentation

Technical deep dive into the architecture, design patterns, and implementation details.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User (CLI Interface)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        Interactive Mode (doe_metrics_client.py)
        • Command parsing
        • Query execution
        • Report generation
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────────┐  ┌───▼─────────┐  ┌──▼─────────────┐
│Cache Mgr   │  │Server Pool  │  │Report Builder  │
│(SQLite)    │  │(Registry)   │  │(Multi-source)  │
└────────────┘  └───┬─────────┘  └────────────────┘
                    │
    ┌───────────────┼───────────────┬──────────────────┐
    │               │               │                  │
┌───▼──────┐  ┌───▼──────┐  ┌──────▼────┐  ┌────────▼──┐
│Google    │  │ Slack    │  │Future APIs │  │Monitoring │
│Docs API  │  │ API      │  │(Phase 2+)  │  │(Logs)     │
└──────────┘  └──────────┘  └────────────┘  └───────────┘
```

## Core Components

### 1. DOEMetricsClient (doe_metrics_client.py)

**Purpose**: Main orchestrator for the entire system.

**Key Classes**:

#### ReportContext
```python
class ReportContext:
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    keywords: List[str]
    sources: List[str]
    theme: str  # incidents, metrics, jobs, general
    results: Dict[str, List[Any]]
```

Tracks state during report generation, allowing queries to share context across multiple servers.

#### DOEMetricsClient
```python
class DOEMetricsClient:
    cache: CacheManager              # Local SQLite cache
    servers: Dict[str, Server]       # Loaded MCP servers
    servers_config: Dict[str, str]   # Server registry (name:path)
    context: ReportContext           # Current report state
    running: bool                    # CLI loop state
```

**Key Methods**:
- `_load_servers_config()` - Parse servers.config
- `load_server()` - Dynamically import and instantiate server
- `connect_servers()` - Load all configured servers
- `execute_query()` - Run query against available servers
- `create_batch_report()` - Multi-step report generation
- `interactive_mode()` - CLI command loop
- `cache_status()` / `clear_cache()` - Cache management

**Async Flow**:
```
interactive_mode()
  ├─ Read user input
  ├─ Parse command
  ├─ Call async handler (execute_query, create_batch_report, etc.)
  ├─ Display results
  └─ Loop back (until exit)
```

### 2. MCP Server Pattern

**Location**: `servers/*.py`

**Standard Structure**:
```python
from fastmcp import Server

server = Server("server_name")

@server.list_tools()
def list_tools() -> list:
    """Return tool schemas"""

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute tool and return JSON"""

async def tool_implementation(arg1, arg2) -> str:
    """Actual tool logic"""
    # 1. Validate input
    # 2. Check cache (optional)
    # 3. Call external API
    # 4. Transform to data model
    # 5. Cache result (optional)
    # 6. Return as JSON
```

**Tool Pattern**:
- Each tool = specific API capability
- Input: Dict[str, Any]
- Output: JSON string
- Error handling: Try-except → JSON error object

**Cache Integration**:
```python
from cache import CacheManager

cache = CacheManager()

# Check cache first
cached = cache.get("source_name", query_string)
if cached:
    return json.dumps({**cached["data"], "cache_hit": True})

# Fetch from API
results = await fetch_from_api(query_string)

# Cache for TTL
cache.set("source_name", query_string, results, ttl_hours=6)

return json.dumps(results)
```

### 3. Cache System (cache/cache_manager.py)

**Purpose**: Local SQLite persistence to reduce API calls.

**Design**:
- **DB Schema**: Single `cache_entries` table with indices
- **Key Fields**:
  - `id`: Unique cache entry ID
  - `source`: API source (google_docs, slack, etc.)
  - `query_hash`: SHA256 hash of query (16 chars)
  - `data_json`: Serialized result
  - `cached_at`: ISO timestamp
  - `expires_at`: ISO timestamp (cached_at + ttl_hours)
  - `ttl_hours`: Time-to-live in hours

**TTL Strategy** (per source, not per query):
```
google_docs:  6 hours  (documents change less frequently)
slack:        2 hours  (conversations are dynamic)
elasticsearch: 1 hour  (metrics are real-time)
slurm:        4 hours  (historical data)
```

**Operations**:
```python
cache.get(source, query)           # → Optional[dict]
cache.set(source, query, data, ttl_hours)  # → None
cache.is_expired(cached_at, ttl_hours)     # → bool
cache.clear_expired()              # → int (deleted count)
cache.list_cached()                # → List[dict]
cache.cache_status()               # → Dict[str, int] (counts per source)
cache.export_cache(format)         # → str (JSON or CSV)
cache.delete_by_source(source)     # → int
cache.clear_all()                  # → int
```

**Concurrency Model**:
- SQLite provides ACID guarantees
- Readers: Concurrent (file-level locking)
- Writers: Sequential (queue management)
- For production scale: Consider PostgreSQL or Redis

### 4. Data Models (models/)

**Base Pattern**:
```python
from pydantic import BaseModel as PydanticBaseModel

class BaseModel(PydanticBaseModel):
    id: str                              # Unique ID
    source: str                          # Source API
    cached_at: Optional[datetime]        # When cached
    cached_from: str                     # Origin reference
```

**Specific Models**:

**Incident**
```python
class Incident(BaseModel):
    title: str
    description: str
    date_found: datetime
    severity: str  # critical|high|medium|low
    systems_affected: List[str]
    resolution_notes: str
    sources: List[str]  # Links to original docs
```

**SlackMessage**
```python
class SlackMessage(BaseModel):
    channel: str
    user: str
    text: str
    timestamp: datetime
    thread_ts: Optional[str]  # Parent message ID
    reactions: List[str]
    reply_count: int
```

**UtilizationMetric**
```python
class UtilizationMetric(BaseModel):
    system: str  # perlmutter, archive, etc.
    metric_type: str  # cpu, gpu, memory, network
    value: float
    unit: str
    status: str  # normal|warning|critical
```

**Job**
```python
class Job(BaseModel):
    job_id: str
    user: str
    status: str  # COMPLETED|FAILED|TIMEOUT|RUNNING
    submit_time: datetime
    end_time: Optional[datetime]
    cpu_count: int
    gpu_count: int
```

**Benefits**:
- Type validation (Pydantic)
- JSON serialization built-in
- IDE autocomplete support
- Clear documentation via schema

## Data Flow Examples

### Query Flow

```
User Input
    ↓
CLI parses command
    ↓
DOEMetricsClient.execute_query()
    ↓
Check cache.get(source, query)
    ├─ Hit? → Return cached + cache_hit=true
    └─ Miss? → Continue
    ↓
Find matching server from loaded servers
    ↓
Server.call_tool("tool_name", arguments)
    ↓
Tool implementation:
    ├─ Validate input
    ├─ Call external API (with auth)
    ├─ Parse response → data model
    └─ Return JSON
    ↓
Cache result cache.set(source, query, results)
    ↓
Return to CLI with cache_hit=false
    ↓
Display to user
```

### Report Generation Flow

```
User: report incidents --from 2025-01-01 --to 2025-01-26
    ↓
CLI parses arguments → ReportContext
    ↓
create_batch_report(theme="incidents", ...)
    ↓
Set context.date_from, context.date_to, etc.
    ↓
Based on theme, call appropriate generator:
    ├─ _generate_incidents_report()
    ├─ _generate_metrics_report()
    ├─ _generate_jobs_report()
    └─ _generate_general_report()
    ↓
Generator queries multiple servers:
    ├─ query("incidents", keywords, date_range)
    ├─ query("slack", keywords, date_range)
    └─ combine results
    ↓
Format output (markdown, JSON, CSV)
    ↓
Return to CLI
    ↓
Display/save report
```

## Server Discovery & Loading

### Configuration (servers.config)

```
# Format: server_name:relative/path/to/server.py
google_docs:servers/google_docs_server.py
slack:servers/slack_server.py
# elasticsearch:servers/elasticsearch_server.py  (commented = disabled)
```

### Dynamic Loading Process

```python
def _load_servers_config():
    # 1. Read servers.config line by line
    # 2. Skip comments (#) and empty lines
    # 3. Parse "name:path" format
    # 4. Return dict {name → path}

async def load_server(name, path):
    # 1. Check if file exists
    # 2. Load module dynamically using importlib
    # 3. Extract 'server' instance from module
    # 4. Store in self.servers[name]
    # 5. Log success/failure

async def connect_servers():
    # For each server in servers_config:
    #   Call load_server()
    # Report total loaded
```

### Benefits
- Add/remove servers without code changes
- No hardcoded imports (lower coupling)
- Easy A/B testing different servers
- Clear registry of active servers

## Error Handling Strategy

### 3-Layer Approach

```
Layer 1: CLI Validation
  ├─ Command exists?
  ├─ Required arguments present?
  └─ Return error to user

Layer 2: Server Try-Except
  ├─ API call in try block
  ├─ Catch all exceptions
  └─ Log error, return JSON with error field

Layer 3: Result Status
  ├─ Check response for error field
  ├─ Display to user with context
  └─ Suggest next steps
```

**Example**:
```python
# CLI validates command
if not subcommand in ["status", "list", "clear"]:
    print("Usage: cache [status|list|clear]")
    return

# Server wraps API call
try:
    results = await external_api.search(query)
except Exception as e:
    logger.error(f"API error: {e}")
    return json.dumps({"error": str(e), "api": "slack"})

# Client checks result
result = json.loads(server_response)
if "error" in result:
    print(f"Error querying {result['api']}: {result['error']}")
else:
    print(f"Found {len(result['results'])} results")
```

## Async/Await Design

**Why Async?**
- Multiple API calls don't block each other
- Single server instance can handle many queries
- Batch reports execute queries in parallel

**Async Pattern**:
```python
async def execute_query(query: str):
    # Create tasks for each server
    tasks = []
    for server_name, server in self.servers.items():
        task = server.call_tool(tool_name, args)
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Combine results
    return combine_results(results)
```

**Interactive Mode**:
```python
async def interactive_mode():
    while self.running:
        user_input = input("DOE_METRICS> ")

        # Parse and get handler
        command, args = parse_input(user_input)
        handler = get_handler(command)

        # Call async handler
        result = await handler(args)

        # Display result
        display(result)
```

## Performance Considerations

### Cache Effectiveness

```
Without cache:
  Each query → API call → 2-10 seconds

With cache (hit):
  Each query → SQLite lookup → <100ms

Typical day:
  5 queries × 5 seconds = 25 seconds
  With cache: First query 5s, rest <100ms total
```

### Scaling Limits

| Component | Limit | Notes |
|-----------|-------|-------|
| Cache DB | 1GB | SQLite file size |
| Cached entries | 100K | Before performance degrades |
| Concurrent queries | 1-5 | SQLite sequential writes |
| API rate limits | Per API | Use cache to minimize |

### Optimization Strategies

1. **Cache TTL tuning** - Adjust per source based on data freshness needs
2. **Batch queries** - Group related searches to hit cache
3. **Index on query_hash** - Already in schema for fast lookups
4. **Archive old cache** - Export and clear cache monthly
5. **Upgrade to PostgreSQL** - For production (supports true concurrency)

## Extension Points

### Adding a New Server

```
1. Copy server_template.py → new_api_server.py
2. Implement list_tools() → tool schemas
3. Implement call_tool() → dispatch to tool methods
4. Implement tool methods → API calls + caching
5. Add to servers.config
6. Restart client
```

### Adding a New Report Theme

```
1. Add theme to create_batch_report() theme parameter
2. Create _generate_[theme]_report() method
3. Query appropriate servers for data
4. Format output (markdown, JSON, CSV)
5. Document in usage examples
```

### Adding Cache for New Source

```
1. Determine TTL (how fresh must data be?)
2. In server tool method:
   - cache.get(source, query)
   - If cached, return
   - Call API
   - cache.set(source, query, data, ttl_hours)
3. Done! (Cache manager handles rest)
```

## Security Considerations

### API Credentials
- Stored in `.env` (not git)
- Read at startup with `load_dotenv()`
- Passed to servers via environment
- Never logged or exposed in errors

### Cache Data
- Stored locally in SQLite file
- File permissions: user-readable only
- No encryption at rest (add if needed)
- No sensitive data in filenames

### Input Validation
- Query strings sanitized (hashed for cache key)
- Command parameters type-checked
- No shell execution (safe from injection)

## Testing Strategy

### Unit Tests (tests/)
- Cache manager CRUD operations
- Expiration logic
- Export formats
- Status aggregation

### Integration Tests (future)
- Server loading and discovery
- End-to-end queries
- Report generation
- Cache hit/miss verification

### Manual Testing Checklist
- [ ] Setup.sh completes without errors
- [ ] start_reporter.sh launches CLI
- [ ] `help` command shows all options
- [ ] Cache commands work (status, list, clear)
- [ ] Search commands return results
- [ ] Reports generate without errors
- [ ] Servers list shows loaded servers
- [ ] Exit command cleanly shuts down

## Deployment Checklist

### Development → Production

- [ ] Replace placeholder API calls
- [ ] Implement proper OAuth2 flow
- [ ] Add database connection pooling
- [ ] Implement rate limiting
- [ ] Set up comprehensive logging
- [ ] Add monitoring/alerting
- [ ] Document operational procedures
- [ ] Create backup strategy for cache.db
- [ ] Implement credential rotation
- [ ] Security audit
- [ ] Performance testing
- [ ] Load testing (if serving multiple users)

---

**Architecture Version:** 1.0
**Last Updated:** 2025-01-26
