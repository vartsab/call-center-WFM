"""Generate an optional SQL Server bulk-load script for full NYC 311 chunks.

The primary, tested local load path is load_raw_nyc_311_pyodbc.py. This script
exists for environments where SQL Server BULK INSERT is configured for local
file access.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def sql_string(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/raw/nyc_311_full_manifest.json")
    parser.add_argument("--output", default="sql/raw/002_bulk_insert_raw_nyc_311_generated.sql")
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    lines = [
        "/*",
        "Optional bulk load script for full NYC 311 chunks.",
        "Run after sql/raw/001_create_raw_nyc_311.sql.",
        "If BULK INSERT is unavailable, use src/data_acquisition/load_raw_nyc_311_pyodbc.py.",
        "*/",
        "",
    ]
    if args.truncate:
        lines.extend(["TRUNCATE TABLE dbo.Raw_NYC_311_Service_Requests;", "GO", ""])

    for chunk in manifest.get("chunks", []):
        path = sql_string(str(Path(str(chunk["path"])).resolve()))
        lines.extend(
            [
                "BULK INSERT dbo.Raw_NYC_311_Service_Requests",
                f"FROM '{path}'",
                "WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '\"', TABLOCK);",
                "GO",
                "",
            ]
        )

    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
