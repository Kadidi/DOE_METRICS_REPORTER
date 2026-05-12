"""Tests for the native utilization backend."""

from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utilization_backend import (
    _compare_summaries,
    _extract_gabor_values,
    UtilizationTrendRequest,
    analyze_utilization_trend,
    build_daily_query,
    build_daily_query_our_logic,
    build_monthly_query,
    build_monthly_query_our_logic,
    choose_report_mode,
)


def test_build_daily_query_matches_bank_app_shape():
    """Daily query should filter on the requested day and host."""
    query = build_daily_query(
        datetime(2026, 1, 15).date(),
        resource="gpu",
        include_root=True,
        cap_only=False,
    )

    assert "FROM usage_2026" in query
    assert "DATETIME_FORMAT(Start, 'yyyy-MM-dd')" in query
    assert "Start >= '2026-01-15'" in query
    assert "Start < '2026-01-16'" in query
    assert "hostname IN ('perlmutter gpu')" in query


def test_build_daily_query_our_logic_uses_avg_zonesize():
    """DOE logic should use AVG(ZoneSize) directly."""
    query = build_daily_query_our_logic(
        datetime(2026, 1, 15).date(),
        resource="gpu",
        include_root=True,
        cap_only=False,
    )

    assert "AVG(ZoneSize)" in query
    assert "SUM(RawHours) AS raw_hours" in query


def test_build_monthly_query_uses_month_denominator():
    """Monthly query should target the month and return its day count."""
    query, days = build_monthly_query(
        datetime(2026, 1, 15).date(),
        resource="cpu",
        include_root=True,
        cap_only=False,
    )

    assert "FROM usage_2026" in query
    assert "hostname IN ('perlmutter cpu')" in query
    assert "Start >= '2026-01-01'" in query
    assert "SUM(RawHours) / (31 * 24 * CASE" in query
    assert days == 31


def test_build_monthly_query_our_logic_uses_avg_zonesize():
    """DOE monthly logic should use AVG(ZoneSize) directly."""
    query, days = build_monthly_query_our_logic(
        datetime(2026, 1, 15).date(),
        resource="cpu",
        include_root=True,
        cap_only=False,
    )

    assert "AVG(ZoneSize)" in query
    assert "SUM(RawHours) AS raw_hours" in query
    assert days == 31


def test_extract_gabor_values_from_email_body():
    """Parse the daily percentages from Gabor's report body."""
    body = """
Yesterday's non-maintenance utilization for Perlmutter (2026-01-15):
host                  util   % capability   queue (days)
---------------------------------------------------------
perlmutter cpu      81.25%          22.10%           0.42
perlmutter gpu      74.50%          15.00%           0.27
"""

    values = _extract_gabor_values(body, datetime(2026, 1, 15).date())

    assert values == {"perlmutter cpu": 81.25, "perlmutter gpu": 74.50}


def test_choose_report_mode_for_day():
    """A one-day range should map to day mode."""
    mode, report_date = choose_report_mode(
        datetime(2026, 1, 15),
        datetime(2026, 1, 15),
    )

    assert mode == "day"
    assert report_date == "2026-01-15"


def test_choose_report_mode_for_month():
    """A same-month range should map to month mode."""
    mode, report_date = choose_report_mode(
        datetime(2026, 1, 1),
        datetime(2026, 1, 31),
    )

    assert mode == "month"
    assert report_date == "2026-01-01"


def test_compare_summaries_reports_differences():
    """Summary comparison should report absolute and relative deltas."""
    result = _compare_summaries(
        {"date": "2026-01-15", "utilization_pct": 70.0},
        {"date": "2026-01-15", "utilization_pct": 80.0},
    )

    assert result["absolute_difference_pct_points"] == -10.0
    assert result["relative_difference_pct"] == -12.5


def test_analyze_utilization_trend_triggers_investigation(monkeypatch):
    """Trend analysis should flag low utilization and sharp drops."""
    samples = {
        "2025-05-04": 97.0,
        "2025-05-05": 96.5,
        "2025-05-06": 96.0,
        "2025-05-07": 95.8,
        "2025-05-08": 95.4,
        "2025-05-09": 93.5,
        "2025-05-10": 92.0,
    }

    class FixedDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return cls(2025, 5, 11)

    def fake_run_report(request):
        pct = samples[request.date]
        return {
            "our_logic": {"summary": {"utilization_pct": pct}},
            "reference_logic": {"summary": {"utilization_pct": pct + 1.0}},
            "comparison": {"summary": {"absolute_difference_pct_points": -1.0}},
        }

    monkeypatch.setattr("utilization_backend.datetime", FixedDatetime)
    monkeypatch.setattr("utilization_backend.run_utilization_report", fake_run_report)

    result = analyze_utilization_trend(UtilizationTrendRequest(resource="gpu", days=7))

    assert result["trend_summary"]["investigation_required"] is True
    assert len(result["trend_summary"]["trigger_reasons"]) >= 2
