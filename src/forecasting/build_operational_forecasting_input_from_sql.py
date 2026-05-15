"""Export full synthetic warehouse forecasting input from SQL Server."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pyodbc


FIELDS = [
    "interval_start_datetime",
    "calendar_date",
    "half_hour_index",
    "day_of_week",
    "is_weekend",
    "is_holiday",
    "service_category",
    "call_volume",
    "avg_handle_time_sec",
]


QUERY = """
SELECT
    CONVERT(varchar(19), Interval_Start_Datetime, 126) AS interval_start_datetime,
    CONVERT(varchar(10), CAST(Interval_Start_Datetime AS date), 126) AS calendar_date,
    Half_Hour_Index AS half_hour_index,
    Day_Of_Week AS day_of_week,
    Is_Weekend AS is_weekend,
    Is_Holiday AS is_holiday,
    Service_Category AS service_category,
    Call_Volume AS call_volume,
    Avg_Handle_Time_Sec AS avg_handle_time_sec
FROM dbo.vw_Forecasting_Input
ORDER BY Interval_Start_Datetime, Service_Category;
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
    parser.add_argument("--output", default="data/processed/full_operational_forecasting_input.csv")
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
                    "half_hour_index": str(row.half_hour_index),
                    "day_of_week": row.day_of_week,
                    "is_weekend": str(row.is_weekend),
                    "is_holiday": str(row.is_holiday),
                    "service_category": row.service_category,
                    "call_volume": str(row.call_volume),
                    "avg_handle_time_sec": f"{float(row.avg_handle_time_sec):.2f}",
                }
            )
            row_count += 1

    cursor.close()
    connection.close()
    print(f"Wrote {row_count:,} rows to {args.output}")


if __name__ == "__main__":
    main()
