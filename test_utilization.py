#!/usr/bin/env python3
"""Direct CLI for testing utilization reports without the LLM layer."""

import argparse
import json
import sys

from utilization_backend import UtilizationRequest, UtilizationReportError, run_utilization_report
from utilization_backend import UtilizationTrendRequest, analyze_utilization_trend


def _format_number(value, digits: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt(row: list[str]) -> str:
        return "  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))

    lines = [fmt(headers), fmt(["-" * width for width in widths])]
    lines.extend(fmt(row) for row in rows)
    return "\n".join(lines)


def _print_report(result: dict) -> None:
    print(f"Source: {result['source']}")
    print(f"Mode: {result['mode']}")
    print(f"Resource: {result['resource']}")
    print(f"Date: {result['date']}")
    print()

    comparison_rows = result["comparison"]["rows"]
    headers = ["label", "hostname", "our %", "reference %", "diff pts", "diff %"]
    rows = []
    for row in comparison_rows:
        label = row.get("date") or row.get("month") or ""
        rel = row.get("relative_difference_pct")
        rows.append(
            [
                label,
                row["hostname"],
                _format_number(row["our_utilization_pct"]),
                _format_number(row["reference_utilization_pct"]),
                _format_number(row["absolute_difference_pct_points"]),
                _format_number(rel) if rel is not None else "",
            ]
        )
    print(_render_table(headers, rows))

    summary = result["comparison"].get("summary")
    if summary:
        print()
        print("Summary")
        print(
            f"  DOE: {_format_number(summary['our_utilization_pct'])}%  "
            f"Reference: {_format_number(summary['reference_utilization_pct'])}%  "
            f"Diff: {_format_number(summary['absolute_difference_pct_points'])} pts"
        )

    gabor = result.get("gabor_comparison")
    if gabor:
        print()
        print("Gabor Comparison")
        if gabor.get("error"):
            print(f"  {gabor['error']}")
        else:
            rel = gabor.get("relative_difference_pct")
            rel_text = "" if rel is None else f" ({_format_number(rel)}%)"
            print(
                f"  Gmail: {_format_number(gabor['gmail_utilization_pct'])}%  "
                f"Reference: {_format_number(gabor['our_utilization_pct'])}%  "
                f"Diff: {_format_number(gabor['absolute_difference_pct_points'])} pts{rel_text}"
            )


def _print_trend(result: dict) -> None:
    print(f"Source: {result['source']}")
    print(f"Resource: {result['resource']}")
    print(
        f"Window: {result['window']['start_date']} to {result['window']['end_date']} "
        f"({result['window']['days']} days)"
    )
    print()

    change_map = {item["to_date"]: item["change_pct_points"] for item in result["day_over_day_changes"]}
    headers = ["date", "our %", "reference %", "our-ref pts", "day/day pts"]
    rows = []
    for row in result["daily_reports"]:
        rows.append(
            [
                row["date"],
                _format_number(row["our_utilization_pct"]),
                _format_number(row["reference_utilization_pct"]),
                _format_number(row["our_vs_reference_pct_points"]),
                _format_number(change_map.get(row["date"])),
            ]
        )
    print(_render_table(headers, rows))

    summary = result["trend_summary"]
    print()
    print("Trend Summary")
    print(f"  Latest utilization: {_format_number(summary['latest_utilization_pct'])}%")
    avg_change = summary.get("average_daily_change_pct_points")
    if avg_change is not None:
        print(f"  Average daily change: {_format_number(avg_change)} pts/day")
    print(f"  Investigation required: {'yes' if summary['investigation_required'] else 'no'}")
    if summary["trigger_reasons"]:
        print("  Trigger reasons:")
        for reason in summary["trigger_reasons"]:
            print(f"    - {reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a daily or monthly utilization report directly."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--day", metavar="YYYY-MM-DD", help="Run a daily utilization report.")
    mode.add_argument("--month", metavar="YYYY-MM-DD", help="Run a monthly utilization report.")
    mode.add_argument("--trend", action="store_true", help="Run a trailing utilization trend analysis.")

    resource = parser.add_mutually_exclusive_group()
    resource.add_argument("--gpu", action="store_true", help="Report GPU utilization.")
    resource.add_argument("--cpu", action="store_true", help="Report CPU utilization.")

    parser.add_argument(
        "--compare-gabor",
        action="store_true",
        help="For daily reports, compare against Gabor's Gmail report.",
    )
    parser.add_argument(
        "--non-root",
        action="store_true",
        help="Exclude root jobs from the calculation.",
    )
    parser.add_argument(
        "--cap-only",
        action="store_true",
        help="Restrict to capability jobs using the bank-app thresholds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON instead of formatted tables.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "day" if args.day else "month"
    date_value = args.day or args.month
    resource = "cpu" if args.cpu else "gpu" if args.gpu else "all"

    if args.trend:
        try:
            result = analyze_utilization_trend(
                UtilizationTrendRequest(
                    resource=resource,
                )
            )
        except UtilizationReportError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            _print_trend(result)
        return 0

    request = UtilizationRequest(
        mode=mode,
        date=date_value,
        resource=resource,
        include_root=not args.non_root,
        cap_only=args.cap_only,
        compare_with_gabor=args.compare_gabor,
    )

    try:
        result = run_utilization_report(request)
    except UtilizationReportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
