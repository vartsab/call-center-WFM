"""Download a full multi-year NYC 311 extract in resumable chunks.

This script is for the real-scale forecasting dataset. It keeps raw files out
of version control and writes one or more CSV chunks per month.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime, timedelta
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


def month_ranges(start_date: date, end_date: date) -> list[tuple[date, date]]:
    ranges: list[tuple[date, date]] = []
    current = date(start_date.year, start_date.month, 1)
    while current <= end_date:
        if current.month == 12:
            next_month = date(current.year + 1, 1, 1)
        else:
            next_month = date(current.year, current.month + 1, 1)
        month_start = max(current, start_date)
        month_end = min(next_month - timedelta(days=1), end_date)
        ranges.append((month_start, month_end))
        current = next_month
    return ranges


def build_url(start_date: date, end_date: date, page_size: int, offset: int) -> str:
    query = {
        "$select": ",".join(DEFAULT_FIELDS),
        "$where": (
            f"created_date between '{start_date.isoformat()}T00:00:00' "
            f"and '{end_date.isoformat()}T23:59:59'"
        ),
        "$order": "created_date,unique_key",
        "$limit": str(page_size),
        "$offset": str(offset),
    }
    return f"{API_URL}?{urlencode(query)}"


def fetch_csv(url: str) -> bytes:
    with urlopen(url, timeout=180) as response:
        return response.read()


def csv_record_count(payload: bytes) -> int:
    lines = payload.splitlines()
    if not lines:
        return 0
    return max(len(lines) - 1, 0)


def write_manifest(path: Path, manifest: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="2023-01-01")
    parser.add_argument("--end-date", default="2025-12-31")
    parser.add_argument("--page-size", type=int, default=50000)
    parser.add_argument("--output-dir", default="data/raw/nyc_311_full")
    parser.add_argument("--manifest-output", default="data/raw/nyc_311_full_manifest.json")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Redownload chunks even when matching files already exist.",
    )
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunks: list[dict[str, object]] = []
    total_records = 0

    for month_start, month_end in month_ranges(start, end):
        part = 0
        while True:
            offset = part * args.page_size
            filename = f"nyc_311_{month_start:%Y_%m}_part{part:04d}.csv"
            output_path = output_dir / filename
            url = build_url(month_start, month_end, args.page_size, offset)

            if output_path.exists() and not args.overwrite:
                payload = output_path.read_bytes()
            else:
                payload = fetch_csv(url)
                output_path.write_bytes(payload)

            record_count = csv_record_count(payload)
            if record_count == 0:
                if output_path.exists():
                    output_path.unlink()
                break

            chunks.append(
                {
                    "path": str(output_path),
                    "start_date": month_start.isoformat(),
                    "end_date": month_end.isoformat(),
                    "offset": offset,
                    "page_size": args.page_size,
                    "record_count": record_count,
                    "url": url,
                }
            )
            total_records += record_count
            print(f"{filename}: {record_count:,} records")

            if record_count < args.page_size:
                break
            part += 1

    manifest = {
        "source": "NYC Open Data - 311 Service Requests from 2020 to Present",
        "api_url": API_URL,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "page_size": args.page_size,
        "output_dir": str(output_dir),
        "chunk_count": len(chunks),
        "record_count": total_records,
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "chunks": chunks,
    }
    write_manifest(Path(args.manifest_output), manifest)
    print(f"Downloaded {total_records:,} records across {len(chunks):,} chunks")
    print(f"Wrote manifest to {args.manifest_output}")


if __name__ == "__main__":
    main()
