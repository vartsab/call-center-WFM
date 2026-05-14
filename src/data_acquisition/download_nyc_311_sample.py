"""Download a small NYC 311 sample for the capstone seed dataset.

The script uses the public Socrata CSV API and writes a reproducible extract
that is small enough for local SQL and modeling iteration.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


API_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
DEFAULT_FIELDS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "location_type",
    "incident_zip",
    "incident_address",
    "city",
    "status",
    "borough",
    "latitude",
    "longitude",
]


def build_url(start_date: str, end_date: str, limit: int) -> str:
    query = {
        "$select": ",".join(DEFAULT_FIELDS),
        "$where": (
            f"created_date between '{start_date}T00:00:00' "
            f"and '{end_date}T23:59:59'"
        ),
        "$order": "created_date",
        "$limit": str(limit),
    }
    return f"{API_URL}?{urlencode(query)}"


def build_daily_counts_url(start_date: str, end_date: str) -> str:
    day_expression = "date_trunc_ymd(created_date)"
    query = {
        "$select": f"{day_expression} as day,count(*) as record_count",
        "$where": (
            f"created_date between '{start_date}T00:00:00' "
            f"and '{end_date}T23:59:59'"
        ),
        "$group": day_expression,
        "$order": "day",
    }
    return f"{API_URL}?{urlencode(query)}"


def fetch_csv(url: str) -> bytes:
    with urlopen(url, timeout=120) as response:
        return response.read()


def download_csv(url: str, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_csv(url)
    output_path.write_bytes(payload)
    return payload.count(b"\n")


def date_range(start_date: str, end_date: str) -> list[date]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def download_daily_sample(start_date: str, end_date: str, daily_limit: int, output_path: Path) -> tuple[int, list[str]]:
    days = date_range(start_date, end_date)
    limits = {day.isoformat(): daily_limit for day in days}
    return download_daily_sample_with_limits(limits, output_path)


def fetch_daily_counts(start_date: str, end_date: str) -> tuple[dict[str, int], str]:
    url = build_daily_counts_url(start_date, end_date)
    payload = fetch_csv(url).decode("utf-8-sig")
    rows = csv.DictReader(StringIO(payload))
    counts: dict[str, int] = {}
    for row in rows:
        day = row["day"][:10]
        counts[day] = int(row["record_count"])
    return counts, url


def allocate_daily_limits(daily_counts: dict[str, int], target_total: int) -> dict[str, int]:
    if target_total <= 0:
        raise ValueError("target_total must be positive")
    total_count = sum(daily_counts.values())
    if total_count <= 0:
        return {day: 0 for day in daily_counts}

    raw_allocations = {
        day: (count / total_count) * target_total
        for day, count in daily_counts.items()
    }
    limits = {day: int(value) for day, value in raw_allocations.items()}
    remaining = target_total - sum(limits.values())
    by_remainder = sorted(
        raw_allocations.items(),
        key=lambda item: item[1] - int(item[1]),
        reverse=True,
    )
    for day, _ in by_remainder[:remaining]:
        limits[day] += 1
    return limits


def download_daily_sample_with_limits(daily_limits: dict[str, int], output_path: Path) -> tuple[int, list[str]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    header: bytes | None = None
    data_lines: list[bytes] = []

    for day, limit in sorted(daily_limits.items()):
        if limit <= 0:
            continue
        url = build_url(day, day, limit)
        urls.append(url)
        payload = fetch_csv(url)
        lines = payload.splitlines()
        if not lines:
            continue
        if header is None:
            header = lines[0]
        data_lines.extend(line for line in lines[1:] if line)

    if header is None:
        output_path.write_bytes(b"")
        return 0, urls

    output_path.write_bytes(b"\n".join([header, *data_lines]) + b"\n")
    return len(data_lines), urls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--end-date", default="2025-01-31")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument(
        "--daily-limit",
        type=int,
        default=0,
        help="If positive, download up to this many rows for each day in the date range.",
    )
    parser.add_argument(
        "--target-total",
        type=int,
        default=0,
        help="If positive, allocate approximately this many rows across days proportional to real daily 311 counts.",
    )
    parser.add_argument(
        "--output",
        default="data/raw/nyc_311_sample.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--metadata-output",
        default="data/raw/nyc_311_sample_metadata.json",
        help="Output metadata JSON path.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    metadata_path = Path(args.metadata_output)

    query_urls: list[str]
    daily_counts: dict[str, int] = {}
    daily_limits: dict[str, int] = {}
    daily_counts_url = ""
    if args.target_total > 0:
        daily_counts, daily_counts_url = fetch_daily_counts(args.start_date, args.end_date)
        daily_limits = allocate_daily_limits(daily_counts, args.target_total)
        record_count, query_urls = download_daily_sample_with_limits(daily_limits, output_path)
    elif args.daily_limit > 0:
        record_count, query_urls = download_daily_sample(
            args.start_date,
            args.end_date,
            args.daily_limit,
            output_path,
        )
    else:
        url = build_url(args.start_date, args.end_date, args.limit)
        line_count = download_csv(url, output_path)
        record_count = max(line_count - 1, 0)
        query_urls = [url]

    metadata = {
        "source": "NYC Open Data - 311 Service Requests from 2020 to Present",
        "api_url": API_URL,
        "query_urls": query_urls,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "limit": args.limit,
        "daily_limit": args.daily_limit,
        "target_total": args.target_total,
        "daily_counts_url": daily_counts_url,
        "daily_counts": daily_counts,
        "daily_limits": daily_limits,
        "output_path": str(output_path),
        "record_count": record_count,
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Downloaded {record_count} records to {output_path}")
    print(f"Wrote metadata to {metadata_path}")


if __name__ == "__main__":
    main()
