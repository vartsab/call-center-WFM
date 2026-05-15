"""Load full NYC 311 chunks into SQL Server with pyodbc batched inserts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

import pyodbc


SQL_COLUMNS = [
    "Unique_Key",
    "Created_Date",
    "Closed_Date",
    "Agency",
    "Agency_Name",
    "Complaint_Type",
    "Descriptor",
    "Location_Type",
    "Incident_Zip",
    "Incident_Address",
    "City",
    "Status",
    "Borough",
    "Latitude",
    "Longitude",
]

CSV_COLUMNS = [
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


def connection_string(server: str, database: str) -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )


def clean(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


def rows_from_chunk(path: Path) -> Iterable[tuple[str | None, ...]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            yield tuple(clean(row.get(column)) for column in CSV_COLUMNS)


def batched(rows: Iterable[tuple[str | None, ...]], batch_size: int) -> Iterable[list[tuple[str | None, ...]]]:
    batch: list[tuple[str | None, ...]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/raw/nyc_311_full_manifest.json")
    parser.add_argument("--server", default="localhost")
    parser.add_argument("--database", default="CallCenterWFM")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    chunks = manifest.get("chunks", [])
    placeholders = ",".join("?" for _ in SQL_COLUMNS)
    columns = ",".join(SQL_COLUMNS)
    insert_sql = f"INSERT INTO dbo.Raw_NYC_311_Service_Requests ({columns}) VALUES ({placeholders})"

    connection = pyodbc.connect(connection_string(args.server, args.database))
    cursor = connection.cursor()
    cursor.fast_executemany = True

    if args.truncate:
        cursor.execute("TRUNCATE TABLE dbo.Raw_NYC_311_Service_Requests")
        connection.commit()

    total_loaded = 0
    for index, chunk in enumerate(chunks, start=1):
        chunk_path = Path(str(chunk["path"]))
        chunk_loaded = 0
        for batch in batched(rows_from_chunk(chunk_path), args.batch_size):
            cursor.executemany(insert_sql, batch)
            connection.commit()
            chunk_loaded += len(batch)
            total_loaded += len(batch)
        print(f"{index}/{len(chunks)} {chunk_path.name}: {chunk_loaded:,} rows loaded; total {total_loaded:,}")

    cursor.close()
    connection.close()
    print(f"Loaded {total_loaded:,} rows into dbo.Raw_NYC_311_Service_Requests")


if __name__ == "__main__":
    main()
