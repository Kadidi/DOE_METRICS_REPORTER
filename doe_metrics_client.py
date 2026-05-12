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
from multi_ask import multi_ask
from llm_summary import summarize_query_results
from utilization_backend import (
    UtilizationReportError,
    UtilizationRequest,
    choose_report_mode,
    run_utilization_report,
)

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
            cached_data = cached["data"]
            if isinstance(cached_data, dict) and "results" in cached_data:
                return {
                    **results,
                    "results": cached_data.get("results", {}),
                    "summary": cached_data.get("summary"),
                    "cache_hit": True,
                }
            return {**results, "results": cached_data, "cache_hit": True}

        # Route the query through the working multi-source Q&A path.
        try:
            qa_results = multi_ask(query_text, verbose=False)
            results["servers_queried"] = [
                source_name
                for source_name, source_result in qa_results.get("sources", {}).items()
                if source_result.get("searched")
            ]
            results["results"] = qa_results
            results["summary"] = summarize_query_results(query_text, qa_results)

            for source_result in qa_results.get("sources", {}).values():
                results["total_results"] += len(source_result.get("results", []))
        except Exception as e:
            logger.error(f"Error executing multi-source query: {e}")
            results["error"] = str(e)
            results["cache_hit"] = False
            return results

        # Cache the results
        self.cache.set(
            "combined_query",
            query_text,
            {"results": results["results"], "summary": results.get("summary")},
            ttl_hours=2,
        )

        results["cache_hit"] = False
        return results

    def _print_query_result(self, result: Dict[str, Any]):
        """Render query results in a readable form."""
        if result.get("error"):
            print(f"Error: {result['error']}")
            return

        if result.get("cache_hit"):
            print("(cached result)")

        if result.get("summary"):
            print("\nAI Summary:")
            print(result["summary"])

        query_results = result.get("results", {})
        routing = query_results.get("routing", {})
        if routing:
            print("\nQuery Debug:")
            matched_rule = routing.get("matched_rule") or "(default)"
            source_order = " -> ".join(routing.get("source_order", []))
            print(f"  Rule: {matched_rule}")
            print(f"  Source order: {source_order}")
            selected_docs = routing.get("selected_google_docs", [])
            if selected_docs:
                print(f"  Google Docs queried: {', '.join(selected_docs)}")
            selected_channels = routing.get("selected_slack_channels", [])
            if selected_channels:
                print(f"  Slack channels queried: {', '.join('#' + name for name in selected_channels)}")

        sources = query_results.get("sources", {})
        if not sources:
            print(json.dumps(result, indent=2))
            return

        printed_any = False

        sfapi_results = sources.get("sfapi", {}).get("results", [])
        if sfapi_results:
            printed_any = True
            print("\nNERSC SF API:")
            for entry in sfapi_results:
                if entry.get("error"):
                    print(f"  Error: {entry['error']}")
                else:
                    print(f"  {entry.get('answer', 'No answer')}")

        google_results = sources.get("google_docs", {}).get("results", [])
        if google_results:
            printed_any = True
            print("\nGoogle Docs:")
            for entry in google_results:
                if entry.get("error"):
                    print(f"  {entry.get('document', 'Document')}: {entry['error']}")
                else:
                    print(f"  {entry.get('document', 'Document')}: {entry.get('answer', 'No answer')}")

        slack_results = sources.get("slack", {}).get("results", [])
        if slack_results:
            printed_any = True
            print("\nSlack:")
            for entry in slack_results:
                if entry.get("error"):
                    print(f"  Error: {entry['error']}")
                else:
                    print(f"  #{entry.get('channel', 'unknown')}: {entry.get('summary', 'No results')}")

        if not printed_any:
            print("No answers were returned for that query.")

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
        resource = "cpu" if "cpu" in [k.lower() for k in self.context.keywords] else "gpu"
        compare_with_gabor = any(
            "gabor" in keyword.lower() or "gmail" in keyword.lower()
            for keyword in self.context.keywords
        )

        try:
            mode, report_date = choose_report_mode(
                self.context.date_from,
                self.context.date_to,
            )
            report_data = run_utilization_report(
                UtilizationRequest(
                    mode=mode,
                    date=report_date,
                    resource=resource,
                    compare_with_gabor=compare_with_gabor and mode == "day",
                )
            )
        except UtilizationReportError as e:
            if output_format == "json":
                return json.dumps(
                    {
                        "title": "System Utilization Report",
                        "error": str(e),
                        "period": {
                            "from": self.context.date_from.isoformat()
                            if self.context.date_from
                            else None,
                            "to": self.context.date_to.isoformat() if self.context.date_to else None,
                        },
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                )
            return "\n".join(
                [
                    "# System Utilization Report",
                    f"**Period:** {self.context.date_from} to {self.context.date_to}",
                    "",
                    f"Error: {e}",
                ]
            )

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
                    "systems": ["perlmutter"],
                    "resource": resource,
                    "mode": report_data["mode"],
                    "our_logic": report_data["our_logic"],
                    "reference_logic": report_data["reference_logic"],
                    "comparison": report_data.get("comparison"),
                    "gabor_comparison": report_data.get("gabor_comparison"),
                    "source": report_data["source"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            )
        else:  # markdown
            lines = [
                "# System Utilization Report",
                f"**Period:** {self.context.date_from} to {self.context.date_to}",
                f"**Resource:** {resource.upper()}",
                f"**Mode:** {report_data['mode']}",
                f"**Source:** {report_data['source']}",
                "",
            ]

            our_summary = report_data["our_logic"].get("summary")
            ref_summary = report_data["reference_logic"].get("summary")
            cmp_summary = report_data.get("comparison", {}).get("summary")
            if our_summary:
                lines.extend(
                    [
                        "## DOE Logic Summary",
                        f"- Utilization: {our_summary.get('utilization_pct', 0):.2f}%",
                        f"- Host count: {our_summary.get('host_count', 0)}",
                        "",
                    ]
                )
            if ref_summary:
                lines.extend(
                    [
                        "## Reference Summary",
                        f"- Utilization: {ref_summary.get('utilization_pct', 0):.2f}%",
                        f"- Host count: {ref_summary.get('host_count', 0)}",
                        "",
                    ]
                )
            if cmp_summary:
                lines.extend(
                    [
                        "## DOE vs Reference",
                        f"- Absolute difference: {cmp_summary.get('absolute_difference_pct_points', 0):.2f} percentage points",
                        (
                            f"- Relative difference: {cmp_summary.get('relative_difference_pct', 0):.2f}%"
                            if cmp_summary.get("relative_difference_pct") is not None
                            else "- Relative difference: n/a"
                        ),
                        "",
                    ]
                )

            if report_data["mode"] == "day":
                lines.append("## Daily Rows")
            else:
                lines.append("## Monthly Rows")
            for row in report_data["comparison"]["rows"]:
                label = row.get("date") or row.get("month")
                rel = row.get("relative_difference_pct")
                rel_text = "n/a" if rel is None else f"{rel:.2f}%"
                lines.append(
                    f"- {label} {row['hostname']}: DOE={row['our_utilization_pct']:.2f}% "
                    f"reference={row['reference_utilization_pct']:.2f}% "
                    f"diff={row['absolute_difference_pct_points']:.2f} pts ({rel_text})"
                )
            comparison = report_data.get("gabor_comparison")
            if comparison:
                lines.append("")
                lines.append("## Gabor Comparison")
                if comparison.get("error"):
                    lines.append(f"- {comparison['error']}")
                else:
                    lines.append(
                        f"- Gmail value: {comparison['gmail_utilization_pct']:.2f}% "
                        f"for {comparison['hostname']}"
                    )
                    lines.append(
                        f"- Our value: {comparison['our_utilization_pct']:.2f}%"
                    )
                    lines.append(
                        f"- Absolute difference: {comparison['absolute_difference_pct_points']:.2f} percentage points"
                    )
                    rel = comparison.get("relative_difference_pct")
                    if rel is not None:
                        lines.append(f"- Relative difference: {rel:.2f}%")
            lines.append("")
            return "\n".join(lines)

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
        print("Ask a question directly, or type 'help' for commands\n")

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
                        self._print_query_result(result)
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
                    result = await self.execute_query(user_input)
                    self._print_query_result(result)

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
