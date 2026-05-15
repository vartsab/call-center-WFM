"""Summarize the full NYC 311 extract manifest and chunk files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_chunks(manifest: dict[str, object]) -> dict[str, object]:
    daily_counts: Counter[str] = Counter()
    complaint_counts: Counter[str] = Counter()
    borough_counts: Counter[str] = Counter()

    for chunk in manifest.get("chunks", []):
        chunk_path = Path(str(chunk["path"]))
        with chunk_path.open("r", newline="", encoding="utf-8-sig") as input_file:
            for row in csv.DictReader(input_file):
                created = row.get("created_date", "")
                if created:
                    daily_counts[created[:10]] += 1
                complaint_counts[row.get("complaint_type", "") or "Unknown"] += 1
                borough_counts[row.get("borough", "") or "Unknown"] += 1

    top_complaints = [
        {"complaint_type": name, "record_count": count}
        for name, count in complaint_counts.most_common(15)
    ]
    top_boroughs = [
        {"borough": name, "record_count": count}
        for name, count in borough_counts.most_common()
    ]
    dates = sorted(daily_counts)
    return {
        "source_record_count": int(manifest.get("record_count", 0)),
        "observed_record_count": sum(daily_counts.values()),
        "date_count": len(dates),
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "average_daily_records": round(sum(daily_counts.values()) / len(dates), 2) if dates else 0,
        "max_daily_records": max(daily_counts.values()) if daily_counts else 0,
        "top_complaint_types": top_complaints,
        "borough_counts": top_boroughs,
        "summarized_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/raw/nyc_311_full_manifest.json")
    parser.add_argument("--summary-output", default="docs/full_dataset_summary.json")
    args = parser.parse_args()

    summary = summarize_chunks(load_manifest(Path(args.manifest)))
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
