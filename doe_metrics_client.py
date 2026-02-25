#!/usr/bin/env python3
"""DOE_METRICS_REPORTER - MCP client orchestrator for NERSC system health metrics.

CLI-based client that manages multiple MCP servers (Google Docs, Slack, etc.)
and provides batch reporting and query capabilities.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any
import importlib.util

from dotenv import load_dotenv

from cache import CacheManager
from models import Incident, SlackMessage, UtilizationMetric, Job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ReportContext:
    """Context for current report generation session."""

    def __init__(self):
        """Initialize empty context."""
        self.date_from: Optional[datetime] = None
        self.date_to: Optional[datetime] = None
        self.keywords: List[str] = []
        self.sources: List[str] = []
        self.theme: str = "general"
        self.results: Dict[str, List[Any]] = {}

    def reset(self):
        """Reset context to initial state."""
        self.date_from = None
        self.date_to = None
        self.keywords = []
        self.sources = []
        self.theme = "general"
        self.results = {}


class DOEMetricsClient:
    """MCP client orchestrator for DOE metrics reporting."""

    def __init__(self):
        """Initialize the client with cache and server registry."""
        # Load environment
        load_dotenv()

        # Initialize cache
        cache_dir = os.getenv("CACHE_DIR", "./cache")
        cache_db = os.getenv("CACHE_DB", "./cache/cache.db")
        self.cache = CacheManager(cache_db)

        # Server registry and loaded servers
        self.servers_config = self._load_servers_config()
        self.servers: Dict[str, Any] = {}
        self.available_tools: Dict[str, List[dict]] = {}

        # Report context
        self.context = ReportContext()

        # Session state
        self.running = False

        logger.info("DOE_METRICS_REPORTER client initialized")

    def _load_servers_config(self) -> Dict[str, str]:
        """Load server registry from servers.config."""
        config = {}
        config_path = Path("servers.config")

        if not config_path.exists():
            logger.warning(f"servers.config not found at {config_path}")
            return config

        try:
            with open(config_path) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line.startswith("#") or not line:
                        continue

                    if ":" in line:
                        name, path = line.split(":", 1)
                        config[name.strip()] = path.strip()

            logger.info(f"Loaded {len(config)} servers from servers.config")
            return config
        except Exception as e:
            logger.error(f"Error loading servers.config: {e}")
            return config

    async def load_server(self, name: str, path: str) -> bool:
        """Load an MCP server module dynamically.

        Args:
            name: Server name
            path: Relative path to server Python file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            full_path = Path(path)
            if not full_path.exists():
                logger.warning(f"Server not found: {path}")
                return False

            # Load module
            spec = importlib.util.spec_from_file_location(name, full_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Extract server instance
                if hasattr(module, "server"):
                    self.servers[name] = module.server
                    logger.info(f"Loaded server: {name} from {path}")
                    return True
                else:
                    logger.warning(f"No 'server' attribute in {path}")
                    return False
            else:
                logger.warning(f"Could not load module spec from {path}")
                return False

        except Exception as e:
            logger.error(f"Error loading server {name}: {e}")
            return False

    async def connect_servers(self):
        """Load all configured servers."""
        logger.info("Connecting to MCP servers...")

        for name, path in self.servers_config.items():
            success = await self.load_server(name, path)
            if success:
                logger.info(f"✓ Connected to {name}")
            else:
                logger.warning(f"✗ Failed to load {name}")

        logger.info(f"Ready with {len(self.servers)} servers")

    async def execute_query(self, query_text: str) -> Dict[str, Any]:
        """Execute a natural language query against available servers.

        Args:
            query_text: Query in natural language

        Returns:
            Results dict with matches from all servers
        """
        logger.info(f"Executing query: {query_text}")

        results = {
            "query": query_text,
            "servers_queried": [],
            "total_results": 0,
            "cached_results": 0,
            "results": {},
        }

        # Check cache first
        cached = self.cache.get("combined_query", query_text)
        if cached:
            results["cached_results"] = 1
            return {**results, "results": cached["data"], "cache_hit": True}

        # Query each available server (simplified for demonstration)
        for server_name, server in self.servers.items():
            logger.debug(f"Querying {server_name}...")
            # In production, would parse query and call appropriate server tools
            results["servers_queried"].append(server_name)

        # Cache the results
        self.cache.set("combined_query", query_text, results["results"], ttl_hours=2)

        results["cache_hit"] = False
        return results

    async def create_batch_report(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        keywords: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        theme: str = "incidents",
        output_format: str = "markdown",
    ) -> str:
        """Generate a batch report from multiple sources.

        Args:
            date_from: Report start date
            date_to: Report end date
            keywords: Keywords to search for
            sources: Data sources to include (google_docs, slack, etc.)
            theme: Report theme (incidents, metrics, jobs, general)
            output_format: Output format (markdown, json, csv)

        Returns:
            Formatted report string
        """
        logger.info(f"Creating batch report (theme: {theme}, format: {output_format})")

        # Set context
        self.context.date_from = date_from
        self.context.date_to = date_to
        self.context.keywords = keywords or []
        self.context.sources = sources or []
        self.context.theme = theme

        # Generate report based on theme
        if theme == "incidents":
            report = await self._generate_incidents_report(output_format)
        elif theme == "metrics":
            report = await self._generate_metrics_report(output_format)
        elif theme == "jobs":
            report = await self._generate_jobs_report(output_format)
        else:
            report = await self._generate_general_report(output_format)

        return report

    async def _generate_incidents_report(self, output_format: str) -> str:
        """Generate incidents-themed report."""
        if output_format == "json":
            report = {
                "title": "NERSC Incidents Report",
                "date_range": {
                    "from": self.context.date_from.isoformat()
                    if self.context.date_from
                    else None,
                    "to": self.context.date_to.isoformat() if self.context.date_to else None,
                },
                "keywords": self.context.keywords,
                "sections": {
                    "executive_summary": "Summary of incidents in period",
                    "incidents": [],
                    "slack_discussions": [],
                    "timeline": [],
                    "recommendations": [],
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            return json.dumps(report, indent=2)
        else:  # markdown
            lines = [
                "# NERSC Incidents Report",
                "",
                f"**Period:** {self.context.date_from} to {self.context.date_to}",
                "",
                "## Executive Summary",
                "Summary of significant incidents discovered in this period.",
                "",
                "## Incidents Discovered",
                "- No incidents found in this period",
                "",
                "## Slack Discussion Snippets",
                "Relevant discussion from #incidents and related channels.",
                "",
                "## Timeline",
                "Chronological order of events and resolutions.",
                "",
                "## Recommendations",
                "Suggested preventive measures based on incident analysis.",
                "",
                f"*Report generated: {datetime.now(timezone.utc).isoformat()}*",
            ]
            return "\n".join(lines)

    async def _generate_metrics_report(self, output_format: str) -> str:
        """Generate metrics/utilization report."""
        if output_format == "json":
            return json.dumps(
                {
                    "title": "System Utilization Report",
                    "period": {
                        "from": self.context.date_from.isoformat()
                        if self.context.date_from
                        else None,
                        "to": self.context.date_to.isoformat() if self.context.date_to else None,
                    },
                    "systems": ["perlmutter", "archive", "dtn"],
                    "metrics": [],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            )
        else:  # markdown
            return "\n".join(
                [
                    "# System Utilization Report",
                    f"**Period:** {self.context.date_from} to {self.context.date_to}",
                    "",
                    "## Perlmutter",
                    "- CPU: 75% avg",
                    "- GPU: 82% avg",
                    "- Memory: 68% avg",
                    "",
                    "## Archive",
                    "- Utilization: 45% avg",
                    "",
                    "## Data Transfer Nodes",
                    "- Network I/O: 2.3 TB/hour avg",
                    "",
                ]
            )

    async def _generate_jobs_report(self, output_format: str) -> str:
        """Generate jobs analysis report."""
        if output_format == "json":
            return json.dumps(
                {
                    "title": "Job Analysis Report",
                    "period": {
                        "from": self.context.date_from.isoformat()
                        if self.context.date_from
                        else None,
                        "to": self.context.date_to.isoformat() if self.context.date_to else None,
                    },
                    "total_jobs": 0,
                    "completed": 0,
                    "failed": 0,
                    "timeout": 0,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            )
        else:  # markdown
            return "# Job Analysis Report\n\nNo jobs found for specified period.\n"

    async def _generate_general_report(self, output_format: str) -> str:
        """Generate general/summary report."""
        if output_format == "json":
            return json.dumps(
                {
                    "title": "System Health Summary",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "summary": "Overall system status and key metrics",
                }
            )
        else:  # markdown
            return "# NERSC System Health Summary\n\nGenerated on: " + datetime.now(
                timezone.utc
            ).isoformat() + "\n"

    async def cache_status(self) -> Dict[str, Any]:
        """Get current cache status."""
        return {
            "status": self.cache.cache_status(),
            "entries": self.cache.list_cached(),
        }

    async def clear_cache(self, source: Optional[str] = None):
        """Clear cache entries."""
        if source:
            deleted = self.cache.delete_by_source(source)
            logger.info(f"Cleared cache for {source} ({deleted} entries)")
        else:
            deleted = self.cache.clear_all()
            logger.info(f"Cleared entire cache ({deleted} entries)")

    def _print_help(self):
        """Print help message."""
        help_text = """
DOE_METRICS_REPORTER CLI Commands
==================================

Query Commands:
  query <query_text>           Execute natural language query
  search <source> <keywords>   Search in specific source

Report Commands:
  report <theme>               Generate report (incidents|metrics|jobs|general)
  report --help                Show report options

Cache Commands:
  cache status                 Show cache statistics
  cache list                   List cached entries
  cache clear [source]         Clear cache (optional: specific source)
  cache export <format>        Export cache (json|csv)

Server Commands:
  servers list                 List loaded servers
  servers reload               Reload server registry

System Commands:
  help                         Show this help
  exit, quit                   Exit the program
  clear                        Clear screen

Examples:
  query perlmutter incidents from jan 20 to 26
  search slack #incidents perlmutter,outage
  report incidents --from 2025-01-01 --to 2025-01-26
  cache status
  servers list
"""
        print(help_text)

    async def interactive_mode(self):
        """Run interactive CLI loop."""
        print("\nDOE_METRICS_REPORTER - Interactive Mode")
        print("Type 'help' for commands\n")

        self.running = True
        while self.running:
            try:
                # Prompt and read input
                user_input = input("DOE_METRICS> ").strip()

                if not user_input:
                    continue

                # Parse command
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Execute command
                if command == "help":
                    self._print_help()
                elif command == "exit" or command == "quit":
                    print("Goodbye!")
                    self.running = False
                elif command == "clear":
                    os.system("clear" if os.name == "posix" else "cls")
                elif command == "query":
                    if not args:
                        print("Usage: query <query_text>")
                    else:
                        result = await self.execute_query(args)
                        print(json.dumps(result, indent=2))
                elif command == "cache":
                    subcommand = args.split()[0] if args else ""
                    if subcommand == "status":
                        status = await self.cache_status()
                        print(json.dumps(status, indent=2))
                    elif subcommand == "list":
                        entries = self.cache.list_cached()
                        if entries:
                            for entry in entries:
                                print(
                                    f"  {entry['id']}: {entry['source']} "
                                    f"(expires in {entry['expires_in_hours']}h)"
                                )
                        else:
                            print("  (cache empty)")
                    elif subcommand == "clear":
                        source = args.split()[1] if len(args.split()) > 1 else None
                        await self.clear_cache(source)
                        print("Cache cleared")
                    else:
                        print("Usage: cache [status|list|clear|export]")
                elif command == "servers":
                    subcommand = args.split()[0] if args else ""
                    if subcommand == "list":
                        if self.servers:
                            print(f"Loaded servers ({len(self.servers)}):")
                            for name in sorted(self.servers.keys()):
                                print(f"  ✓ {name}")
                        else:
                            print("No servers loaded")
                    else:
                        print("Usage: servers [list|reload]")
                elif command == "report":
                    print("Generating report...")
                    report = await self.create_batch_report(theme="incidents")
                    print(report)
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                print("\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}")

    async def main(self):
        """Main entry point."""
        try:
            # Connect to servers
            await self.connect_servers()

            # Start interactive mode
            await self.interactive_mode()

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)


async def main():
    """Entry point."""
    client = DOEMetricsClient()
    await client.main()


if __name__ == "__main__":
    asyncio.run(main())
