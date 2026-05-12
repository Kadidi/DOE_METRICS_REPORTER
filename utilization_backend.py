"""Native DOE Metrics Reporter utilization backend."""

from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Optional

import requests
from requests.auth import HTTPBasicAuth


class UtilizationReportError(RuntimeError):
    """Raised when a utilization report cannot be generated."""


DEFAULT_TIME_ZONE = "US/Pacific"
DEFAULT_ES_HOSTS = ["https://iris.nersc.gov"]
DEFAULT_KIBANA_BASE = "https://iris.nersc.gov/kb"
DEFAULT_KBN_VERSION = "9.1.2"
DEFAULT_MAX_NODES = {
    "perlmutter cpu": 3072,
    "perlmutter gpu": 1792,
    "pod cpu": 256,
    "pod gpu": 128,
}
DEFAULT_HOSTS_BY_RESOURCE = {
    "all": ["perlmutter cpu", "perlmutter gpu"],
    "cpu": ["perlmutter cpu"],
    "gpu": ["perlmutter gpu"],
}


@dataclass
class UtilizationRequest:
    """Normalized utilization query parameters."""

    mode: str
    date: str
    resource: str = "all"
    include_root: bool = True
    cap_only: bool = False
    compare_with_gabor: bool = False
    include_reference_comparison: bool = True


@dataclass
class UtilizationTrendRequest:
    """Parameters for utilization trend analysis."""

    resource: str = "all"
    days: int = 7
    include_root: bool = True
    cap_only: bool = False
    latest_utilization_threshold_pct: float = 95.0
    max_daily_drop_pct_points: float = 1.0


def validate_mode(mode: str) -> str:
    """Validate the requested report mode."""
    normalized = (mode or "").strip().lower()
    if normalized not in {"day", "month"}:
        raise UtilizationReportError(
            f"Unsupported utilization mode '{mode}'. Supported modes: day, month."
        )
    return normalized


def validate_resource(resource: str) -> str:
    """Validate the requested resource preset."""
    normalized = (resource or "").strip().lower()
    if normalized not in DEFAULT_HOSTS_BY_RESOURCE:
        raise UtilizationReportError(
            f"Unsupported resource '{resource}'. Supported resources: all, gpu, cpu."
        )
    return normalized


def parse_date(date_value: str) -> date:
    """Parse a YYYY-MM-DD date string."""
    try:
        parsed = datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError as exc:
        raise UtilizationReportError(
            f"Invalid date '{date_value}'. Expected YYYY-MM-DD."
        ) from exc
    return parsed.date()


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _get_es_hosts() -> list[str]:
    raw = os.getenv("ELASTICSEARCH_HOSTS")
    if not raw:
        return DEFAULT_ES_HOSTS
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UtilizationReportError(
            "ELASTICSEARCH_HOSTS must be a JSON array of URLs."
        ) from exc
    if not isinstance(parsed, list) or not parsed:
        raise UtilizationReportError("ELASTICSEARCH_HOSTS must contain at least one host.")
    return [str(host).rstrip("/") for host in parsed]


def _get_es_auth() -> Optional[HTTPBasicAuth]:
    user = os.getenv("ES_USER")
    password = os.getenv("ES_PASSWD")
    if not password and os.getenv("ELASTIC_PASSWORD_FILE"):
        try:
            password = Path(os.environ["ELASTIC_PASSWORD_FILE"]).expanduser().read_text().splitlines()[0].strip()
        except Exception as exc:
            raise UtilizationReportError(
                f"Could not read ELASTIC_PASSWORD_FILE: {exc}"
            ) from exc
    if user and password:
        return HTTPBasicAuth(user, password)
    return None


def es_sql_query(query: str, time_zone: str = DEFAULT_TIME_ZONE) -> list[list[Any]]:
    """Run an Elasticsearch SQL query and return rows."""
    kibana_base = os.getenv("KIBANA_BASE", DEFAULT_KIBANA_BASE).rstrip("/")
    kbn_version = os.getenv("KBN_VERSION", DEFAULT_KBN_VERSION)
    proxy_url = (
        f"{kibana_base}/api/console/proxy?path=%2F_sql%3Fformat%3Djson&method=POST"
    )
    response = requests.post(
        proxy_url,
        json={"query": query, "time_zone": time_zone},
        auth=_get_es_auth(),
        headers={
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
            "kbn-version": kbn_version,
            "x-elastic-internal-origin": "Kibana",
            "elastic-api-version": "1",
        },
        timeout=60,
    )
    if response.ok:
        payload = response.json()
        return payload.get("rows", [])
    detail = response.text.strip() or response.reason
    raise UtilizationReportError(
        f"Elasticsearch SQL query failed: {response.status_code} {detail}"
    )


def _zone_size_case_expression() -> str:
    whens = "\n".join(
        [
            f"WHEN hostname = '{host}' THEN AVG(COALESCE(ZoneSize, {nodes}))"
            for host, nodes in DEFAULT_MAX_NODES.items()
        ]
    )
    return f"CASE\n{whens}\nEND"


def _host_filter(resource: str) -> str:
    hosts = DEFAULT_HOSTS_BY_RESOURCE[resource]
    return ", ".join(_sql_string(host) for host in hosts)


def _utilization_expression(days: int) -> str:
    return f"SUM(RawHours) / ({days} * 24 * {_zone_size_case_expression()})"


def _our_utilization_expression(days: int) -> str:
    return f"SUM(RawHours) / ({days} * 24 * AVG(ZoneSize))"


def _base_filter(start_day: date, end_day: date, include_root: bool, cap_only: bool) -> str:
    clauses = [
        f"Start >= '{start_day:%Y-%m-%d}'",
        f"Start < '{end_day:%Y-%m-%d}'",
    ]
    if not include_root:
        clauses.append("User != 'root'")
    if cap_only:
        clauses.append(
            "((hostname = 'perlmutter cpu' AND AllocNodes >= 256) OR "
            "(hostname = 'perlmutter gpu' AND AllocNodes >= 128))"
        )
    clauses.append(
        "("
        "hostname IN ('pod cpu', 'pod gpu') OR "
        "("
        "hostname IN ('perlmutter cpu', 'perlmutter gpu') AND "
        "((Start >= '2024-12-05' AND \"ZoneName.keyword\" IN ('gpu', 'cpu')) OR "
        "(Start < '2024-12-05'))"
        ")"
        ")"
    )
    return "\n    AND ".join(clauses)


def build_daily_query(target_day: date, resource: str, include_root: bool, cap_only: bool) -> str:
    """Build the daily SQL query aligned with nersc-bank-app."""
    next_day = target_day + timedelta(days=1)
    year = target_day.year
    return f"""
SELECT
    DATETIME_FORMAT(Start, 'yyyy-MM-dd') AS day,
    hostname,
    {_utilization_expression(1)} AS utilization
FROM usage_{year}
WHERE
    {_base_filter(target_day, next_day, include_root, cap_only)}
    AND hostname IN ({_host_filter(resource)})
GROUP BY 1, 2
ORDER BY 1, 2
""".strip()


def build_daily_query_our_logic(
    target_day: date,
    resource: str,
    include_root: bool,
    cap_only: bool,
) -> str:
    """Build the daily SQL query for DOE reporter's native logic."""
    next_day = target_day + timedelta(days=1)
    year = target_day.year
    return f"""
SELECT
    DATETIME_FORMAT(Start, 'yyyy-MM-dd') AS day,
    hostname,
    {_our_utilization_expression(1)} AS utilization,
    SUM(RawHours) AS raw_hours,
    AVG(ZoneSize) AS avg_zone_size
FROM usage_{year}
WHERE
    {_base_filter(target_day, next_day, include_root, cap_only)}
    AND hostname IN ({_host_filter(resource)})
GROUP BY 1, 2
ORDER BY 1, 2
""".strip()


def build_monthly_query(target_day: date, resource: str, include_root: bool, cap_only: bool) -> tuple[str, int]:
    """Build the monthly SQL query aligned with nersc-bank-app."""
    month_start = target_day.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)

    now = datetime.now(timezone.utc).date()
    if month_start.year == now.year and month_start.month == now.month:
        days = max((now - month_start).days, 1)
    else:
        days = (month_end - month_start).days

    return (
        f"""
SELECT
    hostname,
    {_utilization_expression(days)} AS utilization
FROM usage_{month_start.year}
WHERE
    {_base_filter(month_start, month_start + timedelta(days=days), include_root, cap_only)}
    AND hostname IN ({_host_filter(resource)})
GROUP BY 1
ORDER BY 1
""".strip(),
        days,
    )


def build_monthly_query_our_logic(
    target_day: date,
    resource: str,
    include_root: bool,
    cap_only: bool,
) -> tuple[str, int]:
    """Build the monthly SQL query for DOE reporter's native logic."""
    month_start = target_day.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)

    days = (month_end - month_start).days
    return (
        f"""
SELECT
    hostname,
    {_our_utilization_expression(days)} AS utilization,
    SUM(RawHours) AS raw_hours,
    AVG(ZoneSize) AS avg_zone_size
FROM usage_{month_start.year}
WHERE
    {_base_filter(month_start, month_end, include_root, cap_only)}
    AND hostname IN ({_host_filter(resource)})
GROUP BY 1
ORDER BY 1
""".strip(),
        days,
    )


def _normalize_daily_rows(rows: list[list[Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": str(row[0]),
                "hostname": str(row[1]),
                "utilization_pct": float(row[2]) * 100.0,
                "utilization_fraction": float(row[2]),
            }
        )
    return normalized


def _normalize_daily_rows_our_logic(rows: list[list[Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": str(row[0]),
                "hostname": str(row[1]),
                "utilization_pct": float(row[2]) * 100.0,
                "utilization_fraction": float(row[2]),
                "raw_hours": float(row[3]),
                "avg_zone_size": None if row[4] is None else float(row[4]),
            }
        )
    return normalized


def _normalize_monthly_rows(rows: list[list[Any]], month_start: date, days: int) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "hostname": str(row[0]),
                "utilization_pct": float(row[1]) * 100.0,
                "utilization_fraction": float(row[1]),
                "days_in_denominator": days,
            }
        )
    return normalized


def _normalize_monthly_rows_our_logic(
    rows: list[list[Any]],
    month_start: date,
    days: int,
) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "hostname": str(row[0]),
                "utilization_pct": float(row[1]) * 100.0,
                "utilization_fraction": float(row[1]),
                "raw_hours": float(row[2]),
                "avg_zone_size": None if row[3] is None else float(row[3]),
                "days_in_denominator": days,
            }
        )
    return normalized


def _compute_summary(rows: list[dict[str, Any]], mode: str, target_day: date) -> Optional[dict[str, Any]]:
    if not rows:
        return None
    avg_pct = sum(row["utilization_pct"] for row in rows) / len(rows)
    avg_fraction = avg_pct / 100.0
    if mode == "day":
        return {
            "date": target_day.strftime("%Y-%m-%d"),
            "utilization_pct": avg_pct,
            "utilization_fraction": avg_fraction,
            "host_count": len(rows),
        }
    return {
        "month": target_day.strftime("%Y-%m"),
        "utilization_pct": avg_pct,
        "utilization_fraction": avg_fraction,
        "host_count": len(rows),
    }


def _compare_rows(
    our_rows: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]],
    mode: str,
) -> list[dict[str, Any]]:
    """Compare our rows with reference rows by hostname."""
    ref_by_host = {row["hostname"]: row for row in reference_rows}
    comparisons = []
    for row in our_rows:
        ref = ref_by_host.get(row["hostname"])
        if not ref:
            continue
        abs_diff = row["utilization_pct"] - ref["utilization_pct"]
        rel_diff = None
        if ref["utilization_pct"] != 0:
            rel_diff = (abs_diff / ref["utilization_pct"]) * 100.0
        entry = {
            "hostname": row["hostname"],
            "our_utilization_pct": row["utilization_pct"],
            "reference_utilization_pct": ref["utilization_pct"],
            "absolute_difference_pct_points": abs_diff,
            "relative_difference_pct": rel_diff,
        }
        if mode == "day":
            entry["date"] = row["date"]
        else:
            entry["month"] = row["month"]
        comparisons.append(entry)
    return comparisons


def _compare_summaries(
    our_summary: Optional[dict[str, Any]],
    reference_summary: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if not our_summary or not reference_summary:
        return None
    abs_diff = our_summary["utilization_pct"] - reference_summary["utilization_pct"]
    rel_diff = None
    if reference_summary["utilization_pct"] != 0:
        rel_diff = (abs_diff / reference_summary["utilization_pct"]) * 100.0
    result = {
        "our_utilization_pct": our_summary["utilization_pct"],
        "reference_utilization_pct": reference_summary["utilization_pct"],
        "absolute_difference_pct_points": abs_diff,
        "relative_difference_pct": rel_diff,
    }
    if "date" in our_summary:
        result["date"] = our_summary["date"]
    if "month" in our_summary:
        result["month"] = our_summary["month"]
    return result


def _build_gabor_query(target_day: date) -> str:
    after_date = (target_day - timedelta(days=2)).strftime("%Y/%m/%d")
    before_date = (target_day + timedelta(days=2)).strftime("%Y/%m/%d")
    return (
        'from:gtorok@lbl.gov subject:"Daily Utilization Report" '
        f"after:{after_date} before:{before_date}"
    )


def _extract_gabor_values(body: str, target_day: date) -> dict[str, float]:
    values: dict[str, float] = {}
    section_match = re.search(
        rf"Yesterday's non-maintenance utilization for Perlmutter \({target_day:%Y-%m-%d}\):(.*?)(?:\n\n|\Z)",
        body,
        re.DOTALL,
    )
    if not section_match:
        return values

    section = section_match.group(1)
    for host in ("perlmutter cpu", "perlmutter gpu"):
        pattern = rf"{re.escape(host)}\s+([0-9]+(?:\.[0-9]+)?)%"
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            values[host] = float(match.group(1))
    return values


def fetch_gabor_daily_comparison(target_day: date, resource: str, our_summary: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Fetch Gabor's daily report email and compare values."""
    if our_summary is None:
        return None

    try:
        from query_gmail import GmailQuerier, HAS_GMAIL_API
    except ImportError:
        return {"error": "query_gmail.py not available"}

    if not HAS_GMAIL_API:
        return {"error": "Gmail API client not configured"}

    try:
        querier = GmailQuerier()
        emails = querier.search_emails(_build_gabor_query(target_day), max_results=5, include_body=True)
    except Exception as exc:
        return {"error": f"Gmail query failed: {exc}"}

    host = DEFAULT_HOSTS_BY_RESOURCE[resource][0]
    for email in emails:
        body = email.get("body", "") or ""
        parsed = _extract_gabor_values(body, target_day)
        if host not in parsed:
            continue

        gmail_pct = parsed[host]
        our_pct = float(our_summary["utilization_pct"])
        abs_diff = our_pct - gmail_pct
        rel_diff = None if gmail_pct == 0 else (abs_diff / gmail_pct) * 100.0
        email_date = email.get("date", "")
        try:
            email_dt = parsedate_to_datetime(email_date).isoformat() if email_date else ""
        except Exception:
            email_dt = email_date

        return {
            "source": "gmail",
            "sender": email.get("from"),
            "subject": email.get("subject"),
            "email_date": email_dt,
            "target_date": target_day.strftime("%Y-%m-%d"),
            "hostname": host,
            "gmail_utilization_pct": gmail_pct,
            "our_utilization_pct": our_pct,
            "absolute_difference_pct_points": abs_diff,
            "relative_difference_pct": rel_diff,
        }

    return {
        "error": (
            f"No parseable Gabor Daily Utilization Report found for {target_day:%Y-%m-%d} "
            f"and host {host}."
        )
    }


def run_utilization_report(request: UtilizationRequest) -> dict[str, Any]:
    """Run a utilization report and return structured data."""
    mode = validate_mode(request.mode)
    resource = validate_resource(request.resource)
    target_day = parse_date(request.date)

    if mode == "day":
        our_rows_raw = es_sql_query(
            build_daily_query_our_logic(target_day, resource, request.include_root, request.cap_only)
        )
        our_rows = _normalize_daily_rows_our_logic(our_rows_raw)
        reference_rows_raw = es_sql_query(
            build_daily_query(target_day, resource, request.include_root, request.cap_only)
        )
        reference_rows = _normalize_daily_rows(reference_rows_raw)
    else:
        our_query, our_days = build_monthly_query_our_logic(
            target_day, resource, request.include_root, request.cap_only
        )
        our_rows_raw = es_sql_query(our_query)
        our_rows = _normalize_monthly_rows_our_logic(our_rows_raw, target_day.replace(day=1), our_days)
        reference_query, reference_days = build_monthly_query(
            target_day, resource, request.include_root, request.cap_only
        )
        reference_rows_raw = es_sql_query(reference_query)
        reference_rows = _normalize_monthly_rows(
            reference_rows_raw, target_day.replace(day=1), reference_days
        )

    our_summary = _compute_summary(our_rows, mode, target_day)
    reference_summary = _compute_summary(reference_rows, mode, target_day)
    comparison_rows = _compare_rows(our_rows, reference_rows, mode)
    comparison_summary = _compare_summaries(our_summary, reference_summary)

    result: dict[str, Any] = {
        "source": "iris_elasticsearch_sql",
        "mode": mode,
        "resource": resource,
        "date": target_day.strftime("%Y-%m-%d"),
        "our_logic": {
            "definition": {
                "numerator": "SUM(RawHours) for jobs whose Start falls within the Pacific day/month window",
                "denominator": "days * 24 * AVG(ZoneSize)",
                "time_zone": DEFAULT_TIME_ZONE,
                "include_root": request.include_root,
                "cap_only": request.cap_only,
            },
            "rows": our_rows,
            "summary": our_summary,
        },
        "reference_logic": {
            "definition": {
                "numerator": "SUM(RawHours) for jobs whose Start falls within the Pacific day/month window",
                "denominator": "days * 24 * AVG(COALESCE(ZoneSize, fallback_max_nodes))",
                "time_zone": DEFAULT_TIME_ZONE,
                "include_root": request.include_root,
                "cap_only": request.cap_only,
                "source_path": "nersc-bank-app/banking/jobs/utilization_report.py",
            },
            "rows": reference_rows,
            "summary": reference_summary,
        },
        "comparison": {
            "rows": comparison_rows,
            "summary": comparison_summary,
        },
    }

    if mode == "day" and request.compare_with_gabor:
        result["gabor_comparison"] = fetch_gabor_daily_comparison(target_day, resource, reference_summary)

    return result


def choose_report_mode(date_from: Optional[datetime], date_to: Optional[datetime]) -> tuple[str, str]:
    """Map a report date range to supported day/month modes."""
    if date_from is None and date_to is None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return "day", today

    start = date_from or date_to
    end = date_to or date_from
    assert start is not None
    assert end is not None

    if start.date() == end.date():
        return "day", start.strftime("%Y-%m-%d")

    if start.year == end.year and start.month == end.month:
        return "month", start.strftime("%Y-%m-%d")

    raise UtilizationReportError(
        "Metrics reports currently support a single day or a single calendar month."
    )


def analyze_utilization_trend(request: UtilizationTrendRequest) -> dict[str, Any]:
    """Analyze utilization over the past N completed Pacific days."""
    resource = validate_resource(request.resource)
    days = max(int(request.days), 2)

    today_utc = datetime.utcnow().date()
    end_day = today_utc - timedelta(days=1)
    start_day = end_day - timedelta(days=days - 1)

    daily_reports = []
    for offset in range(days):
        day = start_day + timedelta(days=offset)
        report = run_utilization_report(
            UtilizationRequest(
                mode="day",
                date=day.strftime("%Y-%m-%d"),
                resource=resource,
                include_root=request.include_root,
                cap_only=request.cap_only,
            )
        )
        summary = report["our_logic"]["summary"]
        reference_summary = report["reference_logic"]["summary"]
        comparison_summary = report["comparison"]["summary"]
        daily_reports.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "our_utilization_pct": None if summary is None else summary["utilization_pct"],
                "reference_utilization_pct": None if reference_summary is None else reference_summary["utilization_pct"],
                "our_vs_reference_pct_points": None
                if comparison_summary is None
                else comparison_summary["absolute_difference_pct_points"],
            }
        )

    day_over_day_changes = []
    for previous, current in zip(daily_reports, daily_reports[1:]):
        if previous["our_utilization_pct"] is None or current["our_utilization_pct"] is None:
            continue
        change = current["our_utilization_pct"] - previous["our_utilization_pct"]
        day_over_day_changes.append(
            {
                "from_date": previous["date"],
                "to_date": current["date"],
                "change_pct_points": change,
            }
        )

    latest = daily_reports[-1]
    trigger_reasons = []
    latest_pct = latest["our_utilization_pct"]
    if latest_pct is not None and latest_pct < request.latest_utilization_threshold_pct:
        trigger_reasons.append(
            f"latest utilization {latest_pct:.2f}% is below {request.latest_utilization_threshold_pct:.2f}%"
        )

    largest_drop = None
    for change in day_over_day_changes:
        if change["change_pct_points"] < -request.max_daily_drop_pct_points:
            if largest_drop is None or change["change_pct_points"] < largest_drop["change_pct_points"]:
                largest_drop = change
    if largest_drop is not None:
        trigger_reasons.append(
            f"day-over-day drop of {abs(largest_drop['change_pct_points']):.2f} percentage points "
            f"from {largest_drop['from_date']} to {largest_drop['to_date']}"
        )

    slope = None
    valid = [row for row in daily_reports if row["our_utilization_pct"] is not None]
    if len(valid) >= 2:
        slope = (valid[-1]["our_utilization_pct"] - valid[0]["our_utilization_pct"]) / (len(valid) - 1)

    return {
        "source": "iris_elasticsearch_sql",
        "resource": resource,
        "time_zone": DEFAULT_TIME_ZONE,
        "window": {
            "start_date": start_day.strftime("%Y-%m-%d"),
            "end_date": end_day.strftime("%Y-%m-%d"),
            "days": days,
        },
        "daily_reports": daily_reports,
        "day_over_day_changes": day_over_day_changes,
        "trend_summary": {
            "latest_utilization_pct": latest_pct,
            "average_daily_change_pct_points": slope,
            "investigation_required": bool(trigger_reasons),
            "trigger_reasons": trigger_reasons,
        },
    }
