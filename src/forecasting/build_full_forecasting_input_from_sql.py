"""Build full-history 30-minute forecasting input from raw NYC 311 SQL data."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pyodbc


FIELDS = [
    "interval_start_datetime",
    "calendar_date",
    "time_id",
    "half_hour_index",
    "day_of_week",
    "is_weekend",
    "call_volume",
]


QUERY = """
SELECT
    CONVERT(varchar(19), Interval_Start_Datetime, 126) AS interval_start_datetime,
    CONVERT(varchar(10), Calendar_Date, 126) AS calendar_date,
    Time_ID AS time_id,
    Half_Hour_Index AS half_hour_index,
    Day_Of_Week AS day_of_week,
    Is_Weekend AS is_weekend,
    Call_Volume AS call_volume
FROM dbo.vw_Raw_NYC_311_Volume_30Min
ORDER BY Interval_Start_Datetime;
"""


def connection_string(server: str, database: str) -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="localhost")
    parser.add_argument("--database", default="CallCenterWFM")
    parser.add_argument("--output", default="data/processed/full_forecasting_input.csv")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    connection = pyodbc.connect(connection_string(args.server, args.database))
    cursor = connection.cursor()
    cursor.execute(QUERY)

    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDS)
        writer.writeheader()
        for row in cursor:
            writer.writerow(
                {
                    "interval_start_datetime": row.interval_start_datetime,
                    "calendar_date": row.calendar_date,
                    "time_id": str(row.time_id).zfill(4),
                    "half_hour_index": str(row.half_hour_index),
                    "day_of_week": row.day_of_week,
                    "is_weekend": str(row.is_weekend),
                    "call_volume": str(row.call_volume),
                }
            )
            row_count += 1

    cursor.close()
    connection.close()
    print(f"Wrote {row_count:,} rows to {args.output}")


if __name__ == "__main__":
    main()
