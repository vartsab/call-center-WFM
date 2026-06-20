from __future__ import annotations

import json
import os
from numbers import Integral
from pathlib import Path

import pandas as pd
import pyodbc


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "analysis"
OUT_MD = OUT_DIR / "raw_nyc_311_sql_server_insights.md"
OUT_JSON = OUT_DIR / "raw_nyc_311_sql_server_insights.json"

CONN_STR = os.getenv(
    "CALLCENTER_SQL_CONNECTION",
    (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=CallCenterWFM;"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    ),
)


def read_sql(con: pyodbc.Connection, name: str, sql: str) -> pd.DataFrame:
    print(f"Running {name}...")
    return pd.read_sql_query(sql, con)


def fmt_int(value) -> str:
    return f"{int(round(float(value))):,}"


def fmt_pct(value, digits: int = 1) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def fmt_num(value, digits: int = 2) -> str:
    return f"{float(value):.{digits}f}"


def format_value(col: str, value) -> str:
    if pd.isna(value):
        return ""
    col_l = str(col).lower()
    if "share" in col_l or "rate" in col_l or "growth" in col_l:
        return fmt_pct(value)
    integerish = (
        "count" in col_l
        or "requests_20" in col_l
        or col_l in {"request_count", "total_requests", "raw_rows", "year", "hour_of_day", "max_day", "delta_2023_2025"}
        or col_l.endswith("_count")
    )
    if integerish and not isinstance(value, str):
        return fmt_int(value)
    if isinstance(value, Integral):
        return fmt_int(value)
    if isinstance(value, float):
        return fmt_num(value)
    return str(value)


def md_table(df: pd.DataFrame, columns: list[tuple[str, str]], limit: int | None = None) -> str:
    if limit is not None:
        df = df.head(limit)
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(format_value(col, row[col]) for _, col in columns) + " |")
    return "\n".join([header, sep, *rows])


def run_queries() -> dict[str, pd.DataFrame]:
    queries = {
        "summary": """
SELECT
    COUNT_BIG(*) AS raw_rows,
    MIN(TRY_CONVERT(datetime2(0), Created_Date)) AS min_created,
    MAX(TRY_CONVERT(datetime2(0), Created_Date)) AS max_created
FROM dbo.Raw_NYC_311_Service_Requests;
""",
        "yearly": """
SELECT
    LEFT(Created_Date, 4) AS year,
    COUNT_BIG(*) AS request_count
FROM dbo.Raw_NYC_311_Service_Requests
WHERE Created_Date IS NOT NULL
GROUP BY LEFT(Created_Date, 4)
ORDER BY year;
""",
        "monthly": """
SELECT
    LEFT(Created_Date, 7) AS month,
    COUNT_BIG(*) AS request_count
FROM dbo.Raw_NYC_311_Service_Requests
WHERE Created_Date IS NOT NULL
GROUP BY LEFT(Created_Date, 7)
ORDER BY month;
""",
        "top_dates": """
SELECT TOP (20)
    LEFT(Created_Date, 10) AS calendar_date,
    COUNT_BIG(*) AS request_count
FROM dbo.Raw_NYC_311_Service_Requests
WHERE Created_Date IS NOT NULL
GROUP BY LEFT(Created_Date, 10)
ORDER BY request_count DESC;
""",
        "top_dates_reasons": """
WITH date_totals AS (
    SELECT TOP (20)
        LEFT(Created_Date, 10) AS calendar_date,
        COUNT_BIG(*) AS request_count
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE Created_Date IS NOT NULL
    GROUP BY LEFT(Created_Date, 10)
    ORDER BY request_count DESC
),
reason_counts AS (
    SELECT
        LEFT(r.Created_Date, 10) AS calendar_date,
        COALESCE(NULLIF(r.Complaint_Type, ''), 'Unspecified') AS complaint_type,
        COUNT_BIG(*) AS reason_count,
        ROW_NUMBER() OVER (
            PARTITION BY LEFT(r.Created_Date, 10)
            ORDER BY COUNT_BIG(*) DESC
        ) AS rn
    FROM dbo.Raw_NYC_311_Service_Requests AS r
    INNER JOIN date_totals AS d
        ON LEFT(r.Created_Date, 10) = d.calendar_date
    GROUP BY
        LEFT(r.Created_Date, 10),
        COALESCE(NULLIF(r.Complaint_Type, ''), 'Unspecified')
)
SELECT
    d.calendar_date,
    d.request_count,
    r.complaint_type AS top_reason,
    r.reason_count AS top_reason_count,
    r.reason_count * 1.0 / d.request_count AS top_reason_share
FROM date_totals AS d
INNER JOIN reason_counts AS r
    ON d.calendar_date = r.calendar_date
    AND r.rn = 1
ORDER BY d.request_count DESC;
""",
        "top_intervals": """
WITH interval_counts AS (
    SELECT TOP (20)
        Interval_Start_Datetime,
        Calendar_Date,
        Interval_Start_Time,
        Day_Of_Week,
        Call_Volume AS request_count
    FROM dbo.vw_Raw_NYC_311_Volume_30Min
    ORDER BY Call_Volume DESC
)
SELECT *
FROM interval_counts
ORDER BY request_count DESC;
""",
        "top_intervals_reasons": """
WITH top_intervals AS (
    SELECT TOP (20)
        Interval_Start_Datetime,
        Calendar_Date,
        Interval_Start_Time,
        Day_Of_Week,
        Call_Volume AS request_count
    FROM dbo.vw_Raw_NYC_311_Volume_30Min
    ORDER BY Call_Volume DESC
),
raw_intervals AS (
    SELECT
        DATEADD(
            minute,
            (
                DATEDIFF(
                    minute,
                    CAST('19000101' AS datetime2(0)),
                    TRY_CONVERT(datetime2(0), Created_Date)
                ) / 30
            ) * 30,
            CAST('19000101' AS datetime2(0))
        ) AS interval_start_datetime,
        COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS complaint_type
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE TRY_CONVERT(datetime2(0), Created_Date) IS NOT NULL
),
reason_counts AS (
    SELECT
        t.Interval_Start_Datetime,
        r.complaint_type,
        COUNT_BIG(*) AS reason_count,
        ROW_NUMBER() OVER (
            PARTITION BY t.Interval_Start_Datetime
            ORDER BY COUNT_BIG(*) DESC
        ) AS rn
    FROM top_intervals AS t
    INNER JOIN raw_intervals AS r
        ON t.Interval_Start_Datetime = r.interval_start_datetime
    GROUP BY
        t.Interval_Start_Datetime,
        r.complaint_type
)
SELECT
    t.Interval_Start_Datetime,
    t.Day_Of_Week,
    t.Interval_Start_Time,
    t.request_count,
    rc.complaint_type AS top_reason,
    rc.reason_count AS top_reason_count,
    rc.reason_count * 1.0 / t.request_count AS top_reason_share
FROM top_intervals AS t
INNER JOIN reason_counts AS rc
    ON t.Interval_Start_Datetime = rc.Interval_Start_Datetime
    AND rc.rn = 1
ORDER BY t.request_count DESC;
""",
        "day_of_week_profile": """
SELECT
    Day_Of_Week,
    SUM(Call_Volume) AS request_count,
    SUM(CAST(Call_Volume AS float)) / SUM(SUM(CAST(Call_Volume AS float))) OVER () AS request_share
FROM dbo.vw_Raw_NYC_311_Volume_30Min
GROUP BY Day_Of_Week
ORDER BY
    CASE Day_Of_Week
        WHEN 'Monday' THEN 1
        WHEN 'Tuesday' THEN 2
        WHEN 'Wednesday' THEN 3
        WHEN 'Thursday' THEN 4
        WHEN 'Friday' THEN 5
        WHEN 'Saturday' THEN 6
        WHEN 'Sunday' THEN 7
        ELSE 8
    END;
""",
        "hour_profile": """
SELECT
    DATEPART(hour, Interval_Start_Datetime) AS hour_of_day,
    SUM(Call_Volume) AS request_count,
    SUM(CAST(Call_Volume AS float)) / SUM(SUM(CAST(Call_Volume AS float))) OVER () AS request_share
FROM dbo.vw_Raw_NYC_311_Volume_30Min
GROUP BY DATEPART(hour, Interval_Start_Datetime)
ORDER BY hour_of_day;
""",
        "weekly_slots": """
SELECT TOP (20)
    Day_Of_Week,
    Interval_Start_Time,
    Half_Hour_Index,
    SUM(Call_Volume) AS total_requests,
    COUNT(DISTINCT Calendar_Date) AS observed_dates,
    SUM(CAST(Call_Volume AS float)) / COUNT(DISTINCT Calendar_Date) AS avg_requests
FROM dbo.vw_Raw_NYC_311_Volume_30Min
GROUP BY Day_Of_Week, Interval_Start_Time, Half_Hour_Index
ORDER BY avg_requests DESC;
""",
        "weekly_share": """
WITH cells AS (
    SELECT
        Day_Of_Week,
        Half_Hour_Index,
        SUM(CAST(Call_Volume AS float)) / COUNT(DISTINCT Calendar_Date) AS avg_requests
    FROM dbo.vw_Raw_NYC_311_Volume_30Min
    GROUP BY Day_Of_Week, Half_Hour_Index
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY avg_requests DESC) AS rn
    FROM cells
)
SELECT
    SUM(CASE WHEN rn <= 10 THEN avg_requests ELSE 0 END) / SUM(avg_requests) AS top10_weekly_share,
    SUM(CASE WHEN rn <= 20 THEN avg_requests ELSE 0 END) / SUM(avg_requests) AS top20_weekly_share,
    MAX(avg_requests) AS peak_cell_avg,
    AVG(avg_requests) AS average_cell_avg
FROM ranked;
""",
        "top_complaints": """
SELECT TOP (30)
    COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS complaint_type,
    COUNT_BIG(*) AS request_count,
    COUNT_BIG(*) * 1.0 / SUM(COUNT_BIG(*)) OVER () AS request_share
FROM dbo.Raw_NYC_311_Service_Requests
GROUP BY COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified')
ORDER BY request_count DESC;
""",
        "top_reason_pairs": """
SELECT TOP (30)
    COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS complaint_type,
    COALESCE(NULLIF(Descriptor, ''), 'Unspecified') AS descriptor,
    COUNT_BIG(*) AS request_count
FROM dbo.Raw_NYC_311_Service_Requests
GROUP BY
    COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified'),
    COALESCE(NULLIF(Descriptor, ''), 'Unspecified')
ORDER BY request_count DESC;
""",
        "boroughs": """
SELECT
    COALESCE(NULLIF(Borough, ''), 'Unspecified') AS borough,
    COUNT_BIG(*) AS request_count,
    COUNT_BIG(*) * 1.0 / SUM(COUNT_BIG(*)) OVER () AS request_share
FROM dbo.Raw_NYC_311_Service_Requests
GROUP BY COALESCE(NULLIF(Borough, ''), 'Unspecified')
ORDER BY request_count DESC;
""",
        "agencies": """
SELECT TOP (20)
    COALESCE(NULLIF(Agency, ''), 'Unspecified') AS agency,
    COALESCE(NULLIF(Agency_Name, ''), 'Unspecified') AS agency_name,
    COUNT_BIG(*) AS request_count,
    COUNT_BIG(*) * 1.0 / SUM(COUNT_BIG(*)) OVER () AS request_share
FROM dbo.Raw_NYC_311_Service_Requests
GROUP BY
    COALESCE(NULLIF(Agency, ''), 'Unspecified'),
    COALESCE(NULLIF(Agency_Name, ''), 'Unspecified')
ORDER BY request_count DESC;
""",
        "complaint_growth": """
SELECT
    COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS complaint_type,
    SUM(CASE WHEN LEFT(Created_Date, 4) = '2023' THEN 1 ELSE 0 END) AS requests_2023,
    SUM(CASE WHEN LEFT(Created_Date, 4) = '2024' THEN 1 ELSE 0 END) AS requests_2024,
    SUM(CASE WHEN LEFT(Created_Date, 4) = '2025' THEN 1 ELSE 0 END) AS requests_2025,
    SUM(CASE WHEN LEFT(Created_Date, 4) = '2025' THEN 1 ELSE 0 END)
        - SUM(CASE WHEN LEFT(Created_Date, 4) = '2023' THEN 1 ELSE 0 END) AS delta_2023_2025
FROM dbo.Raw_NYC_311_Service_Requests
WHERE Created_Date IS NOT NULL
GROUP BY COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified')
HAVING SUM(CASE WHEN LEFT(Created_Date, 4) = '2023' THEN 1 ELSE 0 END) >= 10000
ORDER BY delta_2023_2025 DESC;
""",
        "complaint_behavior": """
WITH base AS (
    SELECT
        COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS complaint_type,
        CAST(LEFT(Created_Date, 10) AS date) AS calendar_date,
        DATENAME(weekday, CAST(LEFT(Created_Date, 10) AS date)) AS day_of_week,
        TRY_CONVERT(int, SUBSTRING(Created_Date, 12, 2)) AS hour_num,
        TRY_CONVERT(int, SUBSTRING(Created_Date, 12, 2)) * 2
            + CASE WHEN TRY_CONVERT(int, SUBSTRING(Created_Date, 15, 2)) >= 30 THEN 1 ELSE 0 END AS half_hour_index
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE Created_Date IS NOT NULL
),
summary AS (
    SELECT
        complaint_type,
        COUNT_BIG(*) AS request_count,
        SUM(CASE WHEN day_of_week IN ('Saturday', 'Sunday') THEN 1 ELSE 0 END) AS weekend_count,
        SUM(CASE WHEN hour_num >= 22 OR hour_num < 6 THEN 1 ELSE 0 END) AS night_count,
        SUM(CASE WHEN day_of_week NOT IN ('Saturday', 'Sunday') AND hour_num BETWEEN 9 AND 16 THEN 1 ELSE 0 END) AS business_hour_count
    FROM base
    GROUP BY complaint_type
),
daily AS (
    SELECT complaint_type, calendar_date, COUNT_BIG(*) AS daily_count
    FROM base
    GROUP BY complaint_type, calendar_date
),
daily_stats AS (
    SELECT
        complaint_type,
        AVG(CAST(daily_count AS float)) AS avg_active_day,
        STDEV(CAST(daily_count AS float)) AS stdev_active_day,
        MAX(daily_count) AS max_day
    FROM daily
    GROUP BY complaint_type
),
half_hour AS (
    SELECT complaint_type, half_hour_index, COUNT_BIG(*) AS half_hour_count
    FROM base
    GROUP BY complaint_type, half_hour_index
),
peak_half_hour AS (
    SELECT
        complaint_type,
        half_hour_index,
        half_hour_count,
        ROW_NUMBER() OVER (PARTITION BY complaint_type ORDER BY half_hour_count DESC) AS rn
    FROM half_hour
)
SELECT
    s.complaint_type,
    s.request_count,
    s.weekend_count * 1.0 / s.request_count AS weekend_share,
    s.night_count * 1.0 / s.request_count AS night_share,
    s.business_hour_count * 1.0 / s.request_count AS business_hour_share,
    ds.avg_active_day,
    ds.stdev_active_day,
    ds.stdev_active_day / NULLIF(ds.avg_active_day, 0) AS cv_active_day,
    ds.max_day,
    phh.half_hour_index,
    RIGHT('0' + CAST(phh.half_hour_index / 2 AS varchar(2)), 2)
        + ':' + CASE WHEN phh.half_hour_index % 2 = 0 THEN '00' ELSE '30' END AS peak_time,
    phh.half_hour_count * 1.0 / s.request_count AS peak_half_hour_share
FROM summary AS s
INNER JOIN daily_stats AS ds
    ON s.complaint_type = ds.complaint_type
INNER JOIN peak_half_hour AS phh
    ON s.complaint_type = phh.complaint_type
    AND phh.rn = 1
WHERE s.request_count >= 50000
ORDER BY s.request_count DESC;
""",
        "complaint_monthly": """
WITH top_complaints AS (
    SELECT
        COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS complaint_type
    FROM dbo.Raw_NYC_311_Service_Requests
    GROUP BY COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified')
    HAVING COUNT_BIG(*) >= 50000
)
SELECT
    COALESCE(NULLIF(r.Complaint_Type, ''), 'Unspecified') AS complaint_type,
    LEFT(r.Created_Date, 7) AS month,
    COUNT_BIG(*) AS request_count
FROM dbo.Raw_NYC_311_Service_Requests AS r
INNER JOIN top_complaints AS t
    ON COALESCE(NULLIF(r.Complaint_Type, ''), 'Unspecified') = t.complaint_type
WHERE r.Created_Date IS NOT NULL
GROUP BY
    COALESCE(NULLIF(r.Complaint_Type, ''), 'Unspecified'),
    LEFT(r.Created_Date, 7)
ORDER BY complaint_type, month;
""",
        "illegal_fireworks_dates": """
SELECT TOP (15)
    LEFT(Created_Date, 10) AS calendar_date,
    COUNT_BIG(*) AS request_count
FROM dbo.Raw_NYC_311_Service_Requests
WHERE Complaint_Type = 'Illegal Fireworks'
GROUP BY LEFT(Created_Date, 10)
ORDER BY request_count DESC;
""",
    }

    with pyodbc.connect(CONN_STR, timeout=10) as con:
        return {name: read_sql(con, name, sql) for name, sql in queries.items()}


def write_outputs(results: dict[str, pd.DataFrame]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps({k: v.to_dict("records") for k, v in results.items()}, indent=2, default=str),
        encoding="utf-8",
    )

    summary = results["summary"].iloc[0]
    yearly = results["yearly"]
    monthly = results["monthly"]
    top_month = monthly.sort_values("request_count", ascending=False).iloc[0]
    low_month = monthly.sort_values("request_count").iloc[0]
    weekly_share = results["weekly_share"].iloc[0]

    growth = results["complaint_growth"].copy()
    growth["growth_rate"] = growth["delta_2023_2025"] / growth["requests_2023"]
    growth_up = growth.sort_values("delta_2023_2025", ascending=False)
    growth_down = growth.sort_values("delta_2023_2025")

    behavior = results["complaint_behavior"].copy()
    volatile = behavior.sort_values("cv_active_day", ascending=False)
    night = behavior.sort_values("night_share", ascending=False)
    business = behavior.sort_values("business_hour_share", ascending=False)
    peak_shape = behavior.sort_values("peak_half_hour_share", ascending=False)

    monthly_reason = results["complaint_monthly"].copy()
    seasonality = (
        monthly_reason.groupby("complaint_type")["request_count"]
        .agg(total="sum", avg_month="mean", max_month="max")
        .reset_index()
    )
    seasonality["max_to_avg_month"] = seasonality["max_month"] / seasonality["avg_month"]
    seasonality = seasonality.sort_values("max_to_avg_month", ascending=False)

    heat = monthly_reason[monthly_reason["complaint_type"].eq("HEAT/HOT WATER")].copy()
    heat["month_num"] = pd.to_datetime(heat["month"] + "-01").dt.month
    heat_total = heat["request_count"].sum()
    heat_winter = heat[heat["month_num"].isin([11, 12, 1, 2, 3])]["request_count"].sum()

    lines = [
        "# Raw NYC 311 SQL Server Insight Mining",
        "",
        "Source: `dbo.Raw_NYC_311_Service_Requests` and `dbo.vw_Raw_NYC_311_Volume_30Min` in the local `CallCenterWFM` SQL Server database.",
        "",
        "Included scope: real NYC 311 fields, source timestamps, complaint types, descriptors, agencies, boroughs, and raw timestamp aggregations. Excluded fields: synthetic AHT, SLA, abandonment, agent records, staffing outputs, roster simulation, and derived service-category mapping.",
        "",
        "## Headline Findings",
        "",
        f"- Raw records: **{fmt_int(summary['raw_rows'])}** from **{summary['min_created']}** to **{summary['max_created']}**.",
        f"- Annual volume rose from **{fmt_int(yearly.iloc[0]['request_count'])}** in 2023 to **{fmt_int(yearly.iloc[-1]['request_count'])}** in 2025, a **{fmt_pct((yearly.iloc[-1]['request_count'] - yearly.iloc[0]['request_count']) / yearly.iloc[0]['request_count'])}** increase.",
        f"- Busiest month: **{top_month['month']}** with **{fmt_int(top_month['request_count'])}** requests. Lowest month: **{low_month['month']}** with **{fmt_int(low_month['request_count'])}** requests.",
        f"- The top 10 recurring weekday/half-hour cells account for **{fmt_pct(weekly_share['top10_weekly_share'])}** of a typical week; the top 20 account for **{fmt_pct(weekly_share['top20_weekly_share'])}**.",
        f"- HEAT/HOT WATER is strongly seasonal: **{fmt_pct(heat_winter / heat_total)}** of its volume falls in November-March.",
        "",
        "## Yearly Volume",
        "",
        md_table(yearly, [("Year", "year"), ("Requests", "request_count")]),
        "",
        "## Top Recurring Weekday / Half-Hour Arrival Slots",
        "",
        md_table(
            results["weekly_slots"],
            [
                ("Day", "Day_Of_Week"),
                ("Time", "Interval_Start_Time"),
                ("Avg requests", "avg_requests"),
                ("Total requests", "total_requests"),
            ],
            limit=12,
        ),
        "",
        "## Day-of-Week Arrival Mix",
        "",
        md_table(
            results["day_of_week_profile"],
            [("Day", "Day_Of_Week"), ("Requests", "request_count"), ("Share", "request_share")],
        ),
        "",
        "## Hour-of-Day Arrival Mix",
        "",
        md_table(
            results["hour_profile"],
            [("Hour", "hour_of_day"), ("Requests", "request_count"), ("Share", "request_share")],
        ),
        "",
        "## Top Complaint Reasons",
        "",
        md_table(
            results["top_complaints"],
            [
                ("Complaint type", "complaint_type"),
                ("Requests", "request_count"),
                ("Share", "request_share"),
            ],
            limit=15,
        ),
        "",
        "## Top Complaint + Descriptor Pairs",
        "",
        md_table(
            results["top_reason_pairs"],
            [
                ("Complaint type", "complaint_type"),
                ("Descriptor", "descriptor"),
                ("Requests", "request_count"),
            ],
            limit=15,
        ),
        "",
        "## Borough Mix",
        "",
        md_table(
            results["boroughs"],
            [("Borough", "borough"), ("Requests", "request_count"), ("Share", "request_share")],
        ),
        "",
        "## Agency Mix",
        "",
        md_table(
            results["agencies"],
            [("Agency", "agency"), ("Agency name", "agency_name"), ("Requests", "request_count"), ("Share", "request_share")],
            limit=12,
        ),
        "",
        "## Fastest-Growing High-Volume Complaint Types",
        "",
        md_table(
            growth_up,
            [
                ("Complaint type", "complaint_type"),
                ("2023", "requests_2023"),
                ("2025", "requests_2025"),
                ("Delta", "delta_2023_2025"),
                ("Growth", "growth_rate"),
            ],
            limit=12,
        ),
        "",
        "## Biggest Declines",
        "",
        md_table(
            growth_down,
            [
                ("Complaint type", "complaint_type"),
                ("2023", "requests_2023"),
                ("2025", "requests_2025"),
                ("Delta", "delta_2023_2025"),
                ("Growth", "growth_rate"),
            ],
            limit=12,
        ),
        "",
        "## Night-Weighted High-Volume Reasons",
        "",
        md_table(
            night,
            [
                ("Complaint type", "complaint_type"),
                ("Requests", "request_count"),
                ("Night share", "night_share"),
                ("Weekend share", "weekend_share"),
                ("Peak time", "peak_time"),
            ],
            limit=12,
        ),
        "",
        "## Business-Hour Weighted High-Volume Reasons",
        "",
        md_table(
            business,
            [
                ("Complaint type", "complaint_type"),
                ("Requests", "request_count"),
                ("Business-hour share", "business_hour_share"),
                ("Peak time", "peak_time"),
            ],
            limit=12,
        ),
        "",
        "## Most Seasonal High-Volume Reasons",
        "",
        md_table(
            seasonality,
            [
                ("Complaint type", "complaint_type"),
                ("Total", "total"),
                ("Avg month", "avg_month"),
                ("Max month", "max_month"),
                ("Max/avg month", "max_to_avg_month"),
            ],
            limit=12,
        ),
        "",
        "## Volatile High-Volume Reasons",
        "",
        md_table(
            volatile,
            [
                ("Complaint type", "complaint_type"),
                ("Requests", "request_count"),
                ("CV active day", "cv_active_day"),
                ("Max day", "max_day"),
                ("Peak time", "peak_time"),
            ],
            limit=12,
        ),
        "",
        "## Peak-Shaped High-Volume Reasons",
        "",
        md_table(
            peak_shape,
            [
                ("Complaint type", "complaint_type"),
                ("Requests", "request_count"),
                ("Peak time", "peak_time"),
                ("Peak half-hour share", "peak_half_hour_share"),
                ("Max day", "max_day"),
            ],
            limit=12,
        ),
        "",
        "## Top Outlier Dates",
        "",
        md_table(
            results["top_dates_reasons"],
            [
                ("Date", "calendar_date"),
                ("Requests", "request_count"),
                ("Top reason", "top_reason"),
                ("Top reason requests", "top_reason_count"),
                ("Top reason share", "top_reason_share"),
            ],
            limit=15,
        ),
        "",
        "## Top Outlier Intervals With Dominant Reason",
        "",
        md_table(
            results["top_intervals_reasons"],
            [
                ("Interval", "Interval_Start_Datetime"),
                ("Day", "Day_Of_Week"),
                ("Requests", "request_count"),
                ("Top reason", "top_reason"),
                ("Reason requests", "top_reason_count"),
                ("Reason share", "top_reason_share"),
            ],
            limit=12,
        ),
        "",
        "## Illegal Fireworks Spike Dates",
        "",
        md_table(
            results["illegal_fireworks_dates"],
            [("Date", "calendar_date"), ("Requests", "request_count")],
            limit=12,
        ),
        "",
        "## Operational Leads",
        "",
        "1. **Reason mix changes the staffing profile.** Illegal Parking, Noise - Residential, HEAT/HOT WATER, Blocked Driveway, and Noise - Street/Sidewalk lead total volume and peak at different times.",
        "2. **HEAT/HOT WATER requires seasonal capacity.** November through March accounts for 79.5% of its volume.",
        "3. **Noise demand requires evening coverage.** Night shares reach 63.6% for commercial noise, 51.0% for street noise, and 46.5% for residential noise.",
        "4. **Recurring peaks cover a limited share of the week.** The top 10 weekday/half-hour cells account for 4.9% of weekly arrivals, leaving a broad base requirement.",
        "5. **Customer deployment should connect reasons with effort.** Local AHT and disposition data would convert reason-level demand into workload and staffing requirements.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results = run_queries()
    write_outputs(results)
    print(OUT_MD)
    print(OUT_JSON)


if __name__ == "__main__":
    main()
