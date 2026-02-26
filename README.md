# DOE_METRICS_REPORTER

An AI-powered metrics reporter for NERSC system health using the Model Context Protocol (MCP) architecture. Inspired by APEXA, designed for easy extensibility to multiple data sources including Google Docs, Slack, Elasticsearch, SLURM, ServiceNow, and more.

## Overview

DOE_METRICS_REPORTER enables system administrators and analysts to:
- **Query multiple sources** - Google Docs, Slack, system metrics, job data, etc.
- **Generate batch reports** - Multi-source incident summaries with historical context
- **Cache efficiently** - Local SQLite cache with configurable TTL per source type
- **Extend easily** - MCP server template makes adding new APIs simple

## Key Features

### Phase 1 (MVP): Core Infrastructure
- ✅ CLI orchestrator with interactive shell
- ✅ Local SQLite caching system with TTL
- ✅ Async I/O throughout for performance
- ✅ Google Docs server (list, search, fetch documents)
- ✅ Slack server (channels, messages, threads, mentions)
- ✅ Type-safe data models (Pydantic)
- ✅ Batch report generation (incidents, metrics, jobs)

### Phase 2: System Metrics & Jobs
-  Elasticsearch integration (CPU/GPU/memory utilization)
-  SLURM sacct server (job analysis and queue metrics)

### Phase 3: Enterprise Integration
-  ServiceNow incidents API
-  Gmail query integration
-  IRIS portal for job metadata

### Future Enhancements
- Web UI dashboard (like APEXA's web_server.py)
- Scheduled automated report generation
- Slack integration for critical alerts
- Multi-user access control

## Architecture

```
User Input (CLI)
    ↓
doe_metrics_client.py (MCP Client Orchestrator)
    ↓
[google_docs_server.py] [slack_server.py] [elasticsearch_server.py, ...]
    ↓
Local Cache (SQLite + JSON)
```

### Components

| Component | Purpose |
|-----------|---------|
| `doe_metrics_client.py` | Main CLI client, server orchestrator, report generator |
| `servers/google_docs_server.py` | Google Docs API integration (MVP) |
| `servers/slack_server.py` | Slack API integration (MVP) |
| `cache/cache_manager.py` | SQLite caching with TTL support |
| `models/` | Pydantic data classes for all entity types |
| `servers.config` | Registry of active MCP servers |

## Quick Start

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation

1. **Clone and setup:**
   ```bash
   cd DOE_METRICS_REPORTER
   chmod +x setup_user.sh start_reporter.sh
   pip install -e .
   ```

2. **Configure API credentials:**
   ```bash
   ./setup_user.sh
   ```
   This creates a `.env` file with placeholders for your API credentials.

3. **Start the reporter:**
   ```bash
   ./start_reporter.sh
   ```

### Basic Usage

```bash
DOE_METRICS> query perlmutter incidents from jan 20 to 26
DOE_METRICS> search slack #incidents perlmutter outage
DOE_METRICS> cache status
DOE_METRICS> report incidents --from 2025-01-01 --to 2025-01-26
```

See [USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) for more examples.

### Slack Q&A Bot

Run a bot that answers questions from Slack mentions and DMs:

```bash
python3 slack_bot.py
```

Required environment:

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

Slack app setup:
- Enable **Socket Mode**
- Add bot scopes: `app_mentions:read`, `channels:history`, `groups:history`, `im:history`, `chat:write`
- Subscribe to bot events: `app_mention`, `message.im`
- Install or reinstall app to workspace

## Configuration

### Environment Variables

Create `.env` from `.env.template` and configure:

```bash
# Google Docs API
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_CREDENTIALS_JSON=/path/to/credentials.json

# Slack API
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...

# Cache settings
CACHE_DIR=./cache
LOG_LEVEL=INFO
```

See [API_CONFIGURATION.md](docs/API_CONFIGURATION.md) for detailed setup instructions.

### Server Registry

Edit `servers.config` to enable/disable MCP servers:

```
# Phase 1 (enabled)
google_docs:servers/google_docs_server.py
slack:servers/slack_server.py

# Phase 2 (commented out until ready)
# elasticsearch:servers/elasticsearch_server.py
# slurm:servers/slurm_server.py
```

## Cache System

DOE_METRICS_REPORTER uses local SQLite caching to reduce API calls:

- **TTL per source**: Google Docs (6h), Slack (2h), Metrics (1h), Jobs (4h)
- **Commands**:
  ```bash
  DOE_METRICS> cache status          # View current cache
  DOE_METRICS> cache list            # List cached entries
  DOE_METRICS> cache clear           # Clear all cache
  DOE_METRICS> cache clear slack     # Clear source-specific cache
  ```

## Extending with New Servers

To add support for a new data source (e.g., ServiceNow):

1. Copy the server template:
   ```bash
   cp servers/server_template.py servers/servicenow_server.py
   ```

2. Implement the tool methods and register tools in `list_tools()`

3. Add to `servers.config`:
   ```
   servicenow:servers/servicenow_server.py
   ```

4. Restart the client to load the new server

See [ADDING_SERVERS.md](docs/ADDING_SERVERS.md) for detailed instructions.

## Report Generation

Generate multi-source batch reports:

```bash
# Incidents report with date range
report incidents --from 2025-01-01 --to 2025-01-26

# System metrics report
report metrics --from 2025-01-20 --to 2025-01-26

# Job analysis report
report jobs --from 2025-01-15

# General summary report
report general
```

Reports include:
- Executive summary
- Incident timeline
- Slack discussion snippets
- Resolution notes
- Impact analysis
- Recommendations for prevention

## Data Models

All cached data uses strongly-typed Pydantic models:

- `Incident` - System incidents and maintenance events
- `SlackMessage` - Chat messages with thread context
- `UtilizationMetric` - CPU/GPU/memory metrics
- `Job` - SLURM job from sacct

## Testing

Run the test suite:

```bash
pytest tests/
pytest tests/test_cache.py -v
pytest tests/test_servers.py -v
```

## Documentation

- [SETUP.md](docs/SETUP.md) - Installation and configuration
- [API_CONFIGURATION.md](docs/API_CONFIGURATION.md) - Getting API credentials
- [ADDING_SERVERS.md](docs/ADDING_SERVERS.md) - How to add new data sources
- [USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) - Query and report examples

## Design Principles

1. **Modularity** - Each API = separate MCP server, zero coupling
2. **Extensibility** - Template pattern makes adding servers trivial
3. **Efficiency** - Local SQLite cache with source-specific TTL
4. **Async** - Non-blocking I/O throughout
5. **Type Safety** - Pydantic models for all data
6. **User-Friendly** - Interactive CLI with helpful prompts

## License

NERSC - 2025

## Support

For issues or feature requests, please report via internal issue tracker or contact the NERSC support team.

---

**Version:** 0.1.0 (MVP Phase)
**Last Updated:** 2025-01-26
