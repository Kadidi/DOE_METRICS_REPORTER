"""Utilization and trend tools backed by native IRIS Elasticsearch SQL queries."""

import json

from utilization_backend import (
    UtilizationReportError,
    UtilizationRequest,
    UtilizationTrendRequest,
    analyze_utilization_trend,
    run_utilization_report,
)


class UtilizationTool:
    """Tool for daily and monthly Perlmutter utilization reports."""

    schema = {
        "name": "report_utilization",
        "description": (
            "Generate Perlmutter utilization reports from IRIS Elasticsearch SQL usage data. "
            "Use this tool for daily or monthly CPU/GPU utilization questions, including "
            "requests like 'today's GPU utilization', 'monthly CPU utilization for January 2026', "
            "or 'daily utilization for 2026-01-15'. The tool computes DOE Metrics Reporter's native "
            "IRIS SQL logic, computes the nersc-bank-app reference logic used by Gabor, and returns "
            "a direct comparison. It can optionally compare the reference result with Gabor's Daily "
            "Utilization Report email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["day", "month"],
                    "description": "Report mode: a single day or the calendar month containing the date.",
                },
                "date": {
                    "type": "string",
                    "description": "Anchor date in YYYY-MM-DD format.",
                },
                "resource": {
                    "type": "string",
                    "enum": ["all", "gpu", "cpu"],
                    "description": "Perlmutter resource preset to report. Default is all hostnames (cpu and gpu).",
                    "default": "all",
                },
                "include_root": {
                    "type": "boolean",
                    "description": "Whether to include root jobs. Default is true to match the total utilization logic.",
                    "default": True,
                },
                "cap_only": {
                    "type": "boolean",
                    "description": "When true, restrict to capability jobs using the bank-app thresholds.",
                    "default": False,
                },
                "compare_with_gabor": {
                    "type": "boolean",
                    "description": (
                        "For daily reports, compare the computed value with Gabor's Daily Utilization "
                        "Report Gmail message and report the difference."
                    ),
                    "default": False,
                },
            },
            "required": ["mode", "date"],
        },
    }

    def execute(self, inputs: dict) -> str:
        """Run the utilization report and return JSON."""
        mode = inputs.get("mode", "day")
        request = UtilizationRequest(
            mode=mode,
            date=inputs.get("date", ""),
            resource=inputs.get("resource", "all"),
            include_root=inputs.get("include_root", True),
            cap_only=inputs.get("cap_only", False),
            compare_with_gabor=inputs.get("compare_with_gabor", False),
        )
        try:
            result = run_utilization_report(request)
        except UtilizationReportError as exc:
            return json.dumps({"error": str(exc)})
        return json.dumps(result)


class UtilizationTrendTool:
    """Tool for 7-day utilization trend analysis."""

    schema = {
        "name": "analyze_utilization_trend",
        "description": (
            "Analyze utilization for the past 7 days and determine whether an investigation is needed. "
            "Use this when the user asks for the recent utilization trend, whether utilization is falling, "
            "or whether the system should be investigated."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "enum": ["all", "gpu", "cpu"],
                    "description": "Perlmutter resource to analyze. Default is all hostnames (cpu and gpu).",
                    "default": "all",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of trailing days to analyze. Default is 7.",
                    "default": 7,
                },
                "latest_utilization_threshold_pct": {
                    "type": "number",
                    "description": "Trigger investigation if latest utilization is below this threshold. Default is 95.",
                    "default": 95.0,
                },
                "max_daily_drop_pct_points": {
                    "type": "number",
                    "description": "Trigger investigation if any day-over-day decrease exceeds this many percentage points. Default is 1.",
                    "default": 1.0,
                },
            },
            "required": [],
        },
    }

    def execute(self, inputs: dict) -> str:
        """Run the trend analysis and return JSON."""
        request = UtilizationTrendRequest(
            resource=inputs.get("resource", "all"),
            days=inputs.get("days", 7),
            latest_utilization_threshold_pct=inputs.get("latest_utilization_threshold_pct", 95.0),
            max_daily_drop_pct_points=inputs.get("max_daily_drop_pct_points", 1.0),
        )
        try:
            result = analyze_utilization_trend(request)
        except UtilizationReportError as exc:
            return json.dumps({"error": str(exc)})
        return json.dumps(result)
