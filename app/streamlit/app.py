"""Streamlit dashboard for the call center workforce management capstone."""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"
SQL_CACHE_VERSION = "demo_aggregated_20260520"


POSTGRES_TABLES = {
    "volume_30min": "dashboard_volume_30min",
    "forecasting_input": "dashboard_forecasting_input",
    "agent_performance": "dashboard_agent_performance",
    "agent_dimension": "dashboard_agent_dimension",
    "baseline_forecast": "forecast_baseline",
    "feature_forecast": "forecast_best_holdout",
    "model_holdout_predictions": "forecast_model_holdout_predictions",
    "future_forecast": "future_forecast",
    "future_model_scenarios": "future_model_scenario_forecasts",
    "staffing_requirements": "staffing_requirements",
    "model_staffing_scenarios": "model_staffing_scenarios",
    "optimized_schedule": "optimized_schedule",
    "schedule_coverage": "schedule_coverage",
}


SQL_QUERIES = {
    "volume_30min": """
        SELECT
            Calendar_Date,
            Time_ID,
            MIN(Interval_Start_Time) AS Interval_Start_Time,
            Half_Hour_Index,
            CAST(NULL AS int) AS Queue_ID,
            'All Queues' AS Queue_Name,
            Service_Category,
            SUM(Offered_Calls) AS Offered_Calls,
            SUM(Answered_Calls) AS Answered_Calls,
            SUM(Abandoned_Calls) AS Abandoned_Calls,
            CASE
                WHEN SUM(Answered_Calls) > 0
                THEN SUM(Avg_Handle_Time_Sec * Answered_Calls) / SUM(Answered_Calls)
                ELSE 0
            END AS Avg_Handle_Time_Sec,
            CASE
                WHEN SUM(Offered_Calls) > 0
                THEN SUM(Avg_Hold_Time_Sec * Offered_Calls) / SUM(Offered_Calls)
                ELSE 0
            END AS Avg_Hold_Time_Sec,
            CASE
                WHEN SUM(Offered_Calls) > 0
                THEN SUM(Service_Level_Rate * Offered_Calls) / SUM(Offered_Calls)
                ELSE 0
            END AS Service_Level_Rate
        FROM dbo.vw_Volume_30Min
        GROUP BY
            Calendar_Date,
            Time_ID,
            Half_Hour_Index,
            Service_Category
    """,
    "forecasting_input": """
        SELECT
            MIN(Interval_Start_Datetime) AS Interval_Start_Datetime,
            0 AS Half_Hour_Index,
            'All' AS Day_Of_Week,
            CAST(0 AS bit) AS Is_Weekend,
            CAST(0 AS bit) AS Is_Holiday,
            Service_Category,
            SUM(Call_Volume) AS Call_Volume,
            CASE
                WHEN SUM(Call_Volume) > 0
                THEN SUM(Avg_Handle_Time_Sec * Call_Volume) / SUM(Call_Volume)
                ELSE 0
            END AS Avg_Handle_Time_Sec
        FROM dbo.vw_Forecasting_Input
        GROUP BY Service_Category
    """,
    "agent_performance": """
        SELECT
            Agent_ID,
            Agent_Name,
            Skill_Group,
            MIN(Calendar_Date) AS Calendar_Date,
            SUM(Handled_Calls) AS Handled_Calls,
            CASE
                WHEN SUM(Handled_Calls) > 0
                THEN SUM(Avg_Handle_Time_Sec * Handled_Calls) / SUM(Handled_Calls)
                ELSE 0
            END AS Avg_Handle_Time_Sec,
            CASE
                WHEN SUM(Handled_Calls) > 0
                THEN SUM(Avg_Talk_Time_Sec * Handled_Calls) / SUM(Handled_Calls)
                ELSE 0
            END AS Avg_Talk_Time_Sec,
            CASE
                WHEN SUM(Handled_Calls) > 0
                THEN SUM(Avg_ACW_Time_Sec * Handled_Calls) / SUM(Handled_Calls)
                ELSE 0
            END AS Avg_ACW_Time_Sec
        FROM dbo.vw_Agent_Performance
        GROUP BY
            Agent_ID,
            Agent_Name,
            Skill_Group
    """,
    "agent_dimension": """
        SELECT
            Agent_ID,
            Agent_Name,
            Skill_Group,
            Employment_Type,
            Active_Flag
        FROM dbo.Dim_Agent
    """,
}


PAPER_BG = "#f8f3ea"
PANEL_BG = PAPER_BG
INK = "#182033"
MUTED = "#6d675d"
RULE = "#d7cec0"
GRID = "#e5dbcd"
ACCENT = "#2f6f9f"
ACCENT_DARK = "#24364b"
ACCENT_WARM = "#b66a36"
ACCENT_SOFT = "#7aaed6"
EDITORIAL_COLORS = [
    ACCENT_DARK,
    ACCENT,
    ACCENT_WARM,
    "#7b766c",
    ACCENT_SOFT,
    "#7c4f3a",
]


def page_config() -> None:
    st.set_page_config(
        page_title="Call Center WFM",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .stApp {
            background: #f8f3ea;
            color: #182033;
        }
        header[data-testid="stHeader"] {
            background: #f2eadf;
            border-bottom: 1px solid #d7cec0;
        }
        div[data-testid="stToolbar"] {
            display: none;
            visibility: hidden;
        }
        div[data-testid="stDecoration"] {
            background: #2f6f9f;
        }
        .block-container {
            padding-top: 1.05rem;
            max-width: 1180px;
        }
        section[data-testid="stSidebar"] {
            width: 18.5rem !important;
            min-width: 18.5rem !important;
            background: #f2eadf;
        }
        section[data-testid="stSidebar"] > div {
            width: 18.5rem !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            border-right: 1px solid #d7cec0;
            padding-top: 1.35rem;
        }
        .sidebar-masthead {
            border-bottom: 1px solid #cfc5b7;
            margin: 0.15rem 0 1rem;
            padding-bottom: 0.95rem;
        }
        .sidebar-eyebrow,
        .sidebar-card-label,
        .sidebar-filter-label {
            color: #6d675d;
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .sidebar-title {
            color: #182033;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.58rem;
            font-weight: 400;
            letter-spacing: 0;
            line-height: 1.05;
            margin-top: 0.35rem;
        }
        .sidebar-summary {
            color: #4d4a44;
            font-size: 0.82rem;
            line-height: 1.45;
            margin-top: 0.65rem;
        }
        .sidebar-source {
            align-items: center;
            display: flex;
            gap: 0.45rem;
            margin-top: 0.75rem;
        }
        .sidebar-source-label {
            color: #6d675d;
            font-size: 0.68rem;
        }
        .sidebar-source-pill {
            background: #e5edf2;
            border: 1px solid #c9d8e2;
            color: #2f5f84;
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            padding: 0.14rem 0.34rem;
            text-transform: uppercase;
        }
        .sidebar-card {
            background: rgba(255, 255, 255, 0.36);
            border: 1px solid #d8cebf;
            border-left: 3px solid #2f6f9f;
            margin: 0.85rem 0 1rem;
            padding: 0.72rem 0.78rem;
        }
        .sidebar-card-title {
            color: #20293a;
            font-size: 0.88rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.25rem;
        }
        .sidebar-card-text {
            color: #555047;
            font-size: 0.76rem;
            line-height: 1.38;
            margin-top: 0.32rem;
        }
        .sidebar-ledger {
            color: #333a45;
            font-size: 0.78rem;
            line-height: 1.35;
        }
        .sidebar-ledger-row {
            border-bottom: 1px solid rgba(215, 206, 192, 0.7);
            padding: 0.48rem 0;
        }
        .sidebar-ledger-row:last-child {
            border-bottom: 0;
        }
        .sidebar-ledger-label {
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            margin-right: 0.3rem;
            text-transform: uppercase;
        }
        .sidebar-ledger-label.real {
            color: #267451;
        }
        .sidebar-ledger-label.synthetic {
            color: #9a5a2e;
        }
        .sidebar-ledger-label.forecasted {
            color: #2f6f9f;
        }
        .sidebar-ledger-label.simulated {
            color: #625d55;
        }
        .sidebar-ledger-note {
            color: #625d55;
            font-size: 0.74rem;
            font-style: italic;
            line-height: 1.35;
            margin-top: 0.55rem;
        }
        .sidebar-filter-label {
            border-top: 1px solid #d7cec0;
            margin: 1rem 0 0.45rem;
            padding-top: 0.85rem;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] details {
            background: rgba(255, 255, 255, 0.34);
            border: 1px solid #d8cebf;
            border-radius: 4px;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary p {
            color: #293141;
            font-size: 0.82rem;
            font-weight: 700;
        }
        section[data-testid="stSidebar"] label p {
            color: #5f5a51;
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }
        [data-baseweb="tag"] {
            background-color: #e8dccd !important;
            border: 1px solid #d0c1b0 !important;
            color: #293141 !important;
        }
        [data-baseweb="tag"] span {
            color: #293141 !important;
            font-weight: 650;
        }
        [data-baseweb="tag"] svg {
            fill: #6d675d !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] div[data-baseweb="input"] > div {
            background: rgba(255, 255, 255, 0.72);
            border-color: #d8cebf;
            border-radius: 4px;
        }
        .app-shell-label {
            color: #6c675d;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin: 0 0 0.4rem;
            text-transform: uppercase;
        }
        div[data-testid="stAppViewContainer"] h1 {
            font-size: 2.05rem;
            font-weight: 600;
            letter-spacing: 0;
            margin-bottom: 0.35rem;
        }
        div[data-testid="stMetric"] {
            padding-bottom: 0.2rem;
        }
        div[data-testid="stMetric"] label {
            color: #4b5563;
        }
        div[data-baseweb="tab-list"] {
            background: #f8f3ea;
            flex-wrap: wrap;
            padding: 0.35rem 0 0;
            row-gap: 0.15rem;
            border-bottom: 1px solid #d7cec0;
        }
        button[data-baseweb="tab"] {
            background: transparent !important;
        }
        button[data-baseweb="tab"] {
            white-space: nowrap;
            padding-left: 0.32rem;
            padding-right: 0.32rem;
        }
        button[data-baseweb="tab"] p {
            font-size: 0.74rem;
            letter-spacing: 0.01em;
        }
        .insight-callout {
            border-left: 4px solid #2f6f9f;
            background: rgba(255, 255, 255, 0.58);
            border-radius: 4px;
            padding: 0.72rem 0.9rem;
            margin: 0.4rem 0 1rem 0;
            color: #1d2638;
            font-size: 0.95rem;
        }
        .pipeline-flow {
            border: 1px solid #dfd6ca;
            border-radius: 4px;
            padding: 0.85rem 1rem;
            background: rgba(255, 255, 255, 0.62);
            color: #111827;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .portfolio-overview {
            padding-top: 1.05rem;
        }
        .portfolio-eyebrow,
        .portfolio-smallcaps,
        .portfolio-kpi-label,
        .portfolio-section-label,
        .portfolio-chip {
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .portfolio-eyebrow {
            color: #6f6a61;
            margin-bottom: 0.38rem;
        }
        .portfolio-title {
            color: #273041;
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(2.15rem, 5vw, 4.05rem);
            font-weight: 400;
            letter-spacing: 0;
            line-height: 0.96;
            margin: 0 0 1.05rem;
        }
        .portfolio-dek {
            color: #414141;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.06rem;
            font-style: italic;
            line-height: 1.65;
            margin: 0 0 1.15rem;
            max-width: 760px;
        }
        .portfolio-meta {
            border-left: 1px solid #bfb4a6;
            color: #343b49;
            margin-top: 1.1rem;
            padding-left: 1rem;
            text-align: right;
        }
        .portfolio-meta-value {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.05rem;
            line-height: 1.25;
        }
        .portfolio-meta-note {
            color: #6d675d;
            font-size: 0.76rem;
            font-style: italic;
            margin-top: 0.25rem;
        }
        .portfolio-rule {
            border: 0;
            border-top: 1px solid #d7cec0;
            margin: 1.1rem 0 1.35rem;
        }
        .portfolio-kpi-grid {
            display: grid;
            gap: 1rem;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            margin: 0.35rem 0 1.45rem;
        }
        .portfolio-kpi {
            border-top: 1px solid #cfc5b7;
            padding-top: 0.72rem;
        }
        .portfolio-kpi-label {
            color: #6d675d;
            line-height: 1.25;
            min-height: 2.1rem;
        }
        .portfolio-kpi-value {
            color: #293141;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 2.2rem;
            font-weight: 400;
            line-height: 1;
            margin-top: 0.45rem;
        }
        .portfolio-kpi-note {
            color: #6f6a61;
            font-size: 0.74rem;
            margin-top: 0.35rem;
        }
        .portfolio-section-label {
            color: #5f5a51;
            margin: 0.15rem 0 0.35rem;
        }
        .portfolio-section-copy {
            color: #4b4b4b;
            font-size: 0.92rem;
            line-height: 1.45;
            margin: 0 0 0.8rem;
        }
        .portfolio-pipeline {
            margin-top: 0.15rem;
        }
        .portfolio-pipeline-step {
            background: rgba(255, 255, 255, 0.62);
            border-left: 3px solid #2f6f9f;
            box-shadow: inset 0 -1px 0 rgba(37, 40, 44, 0.06);
            margin-bottom: 0.78rem;
            padding: 0.72rem 0.75rem 0.7rem;
        }
        .portfolio-pipeline-step.synthetic {
            border-left-color: #b66a36;
        }
        .portfolio-pipeline-step.forecasted {
            border-left-color: #2f6f9f;
        }
        .portfolio-pipeline-step.simulated {
            border-left-color: #7b766c;
        }
        .portfolio-step-row {
            align-items: center;
            display: flex;
            gap: 0.75rem;
            justify-content: space-between;
        }
        .portfolio-step-title {
            color: #293141;
            font-size: 0.87rem;
            font-weight: 650;
            line-height: 1.25;
        }
        .portfolio-step-note {
            color: #5f5a51;
            font-size: 0.74rem;
            line-height: 1.35;
            margin-top: 0.18rem;
        }
        .portfolio-chip {
            background: #efe8dc;
            border-radius: 2px;
            color: #5a554e;
            flex: 0 0 auto;
            letter-spacing: 0.08em;
            padding: 0.18rem 0.35rem;
        }
        .portfolio-chip.real {
            background: #dbeee6;
            color: #267451;
        }
        .portfolio-chip.synthetic {
            background: #f2e2d2;
            color: #9a5a2e;
        }
        .portfolio-chip.forecasted {
            background: #dfeaf5;
            color: #2f6f9f;
        }
        .portfolio-chip.simulated {
            background: #e9e4dc;
            color: #625d55;
        }
        .portfolio-transparency {
            border-top: 1px solid #d7cec0;
            color: #54504a;
            font-size: 0.82rem;
            line-height: 1.45;
            margin-top: 1.2rem;
            padding-top: 0.85rem;
        }
        .chapter-header {
            border-bottom: 1px solid #d7cec0;
            margin: 1.2rem 0 1.35rem;
            padding-bottom: 1.05rem;
        }
        .chapter-kicker {
            color: #6f6a61;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
        }
        .chapter-title {
            color: #273041;
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(1.85rem, 3.2vw, 3.05rem);
            font-weight: 400;
            letter-spacing: 0;
            line-height: 1.02;
            margin: 0;
        }
        .chapter-dek {
            color: #414141;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1rem;
            font-style: italic;
            line-height: 1.55;
            margin: 0.65rem 0 0;
            max-width: 820px;
        }
        .chapter-tag {
            background: #efe8dc;
            color: #5a554e;
            display: inline-block;
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            margin-top: 0.85rem;
            padding: 0.22rem 0.42rem;
            text-transform: uppercase;
        }
        .editorial-metric-grid {
            display: grid;
            gap: 1rem;
            grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
            margin: 0.35rem 0 1.35rem;
        }
        .editorial-metric {
            border-top: 1px solid #cfc5b7;
            min-width: 0;
            padding-top: 0.65rem;
        }
        .editorial-metric-label {
            color: #6d675d;
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            line-height: 1.22;
            min-height: 1.65rem;
            text-transform: uppercase;
        }
        .editorial-metric-value {
            color: #1d2638;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 2rem;
            font-weight: 400;
            line-height: 1;
            margin-top: 0.45rem;
            overflow-wrap: anywhere;
        }
        .editorial-metric-note {
            color: #6f6a61;
            font-size: 0.73rem;
            margin-top: 0.35rem;
        }
        .editorial-section,
        .chart-label {
            color: #5f5a51;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin: 1.25rem 0 0.4rem;
            text-transform: uppercase;
        }
        .editorial-note,
        .chart-note {
            color: #4b4b4b;
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 0.75rem;
            max-width: 820px;
        }
        .insight-callout .callout-label {
            color: #5f5a51;
            display: block;
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
        }
        .method-flow {
            display: grid;
            gap: 0.7rem;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            margin: 0.5rem 0 1.3rem;
        }
        .method-card {
            background: rgba(255, 255, 255, 0.62);
            border-left: 3px solid #2f6f9f;
            color: #293141;
            min-height: 5.2rem;
            padding: 0.8rem 0.8rem 0.7rem;
        }
        .method-card.synthetic {
            border-left-color: #b66a36;
        }
        .method-card.simulated {
            border-left-color: #7b766c;
        }
        .method-card-title {
            font-size: 0.86rem;
            font-weight: 700;
            line-height: 1.25;
        }
        .method-card-note {
            color: #5f5a51;
            font-size: 0.74rem;
            line-height: 1.35;
            margin-top: 0.25rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #dfd6ca;
            border-radius: 4px;
        }
        div[data-testid="stPlotlyChart"],
        div[data-testid="stPlotlyChart"] > div {
            background: #f8f3ea !important;
        }
        @media (max-width: 900px) {
            .portfolio-kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .portfolio-meta {
                text-align: left;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_first_json(paths: list[Path]) -> dict[str, Any]:
    for path in paths:
        summary = load_json(path)
        if summary:
            return summary
    return {}


def sql_connection_string() -> str:
    return os.getenv(
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


def postgres_connection_string() -> str:
    return os.getenv("DATABASE_URL", "")


def dashboard_source_mode() -> str:
    mode = os.getenv("CALLCENTER_DASHBOARD_SOURCE", "auto").strip().lower()
    if mode not in {"auto", "sql", "csv", "postgres"}:
        return "auto"
    return mode


def password_is_configured() -> bool:
    return bool(os.getenv("WFM_DEMO_PASSWORD", "").strip())


def authenticate() -> bool:
    expected_password = os.getenv("WFM_DEMO_PASSWORD", "").strip()
    if not expected_password:
        return True
    if st.session_state.get("authenticated"):
        return True

    st.title("Call Center Workforce Management")
    with st.form("demo_password_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

    if submitted:
        if password == expected_password:
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Incorrect password.")
    return False


@st.cache_resource(show_spinner=False)
def get_sql_connection() -> Any | None:
    try:
        import pyodbc
    except ImportError:
        return None

    try:
        return pyodbc.connect(sql_connection_string(), timeout=5)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def get_postgres_connection() -> Any | None:
    connection_string = postgres_connection_string()
    if not connection_string:
        return None
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        return None
    try:
        return psycopg.connect(connection_string, row_factory=dict_row)
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def read_sql_cached(query_key: str, cache_version: str) -> pd.DataFrame:
    connection = get_sql_connection()
    if connection is None:
        return pd.DataFrame()
    cursor = connection.cursor()
    cursor.execute(SQL_QUERIES[query_key])
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    return pd.DataFrame.from_records(rows, columns=columns)


@st.cache_data(show_spinner=False)
def read_postgres_cached(table_key: str, cache_version: str) -> pd.DataFrame:
    table_name = POSTGRES_TABLES[table_key]
    connection = get_postgres_connection()
    if connection is None:
        return pd.DataFrame()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
    return pd.DataFrame.from_records(rows)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return read_csv_cached(str(path), path.stat().st_mtime_ns)


def read_sql(query_key: str) -> pd.DataFrame:
    return read_sql_cached(query_key, SQL_CACHE_VERSION)


def read_postgres(table_key: str) -> pd.DataFrame:
    return read_postgres_cached(table_key, SQL_CACHE_VERSION)


@st.cache_data(show_spinner=False)
def read_csv_cached(path: str, cache_version: int) -> pd.DataFrame:
    return pd.read_csv(path)


def read_first_csv(paths: list[Path]) -> pd.DataFrame:
    for path in paths:
        data = read_csv(path)
        if not data.empty:
            return data
    return pd.DataFrame()


def read_postgres_or_first_csv(table_key: str, paths: list[Path]) -> pd.DataFrame:
    if dashboard_source_mode() == "postgres":
        data = read_postgres(table_key)
        if not data.empty:
            return data
    return read_first_csv(paths)


def model_label(model_name: str) -> str:
    return model_name.replace("_", " ").title()


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            output.append(value)
            seen.add(value)
    return output


def load_sql_data() -> dict[str, pd.DataFrame]:
    return {
        "volume_30min": read_sql("volume_30min"),
        "forecasting_input": read_sql("forecasting_input"),
        "agent_performance": read_sql("agent_performance"),
        "agent_dimension": read_sql("agent_dimension"),
    }


def load_postgres_data() -> dict[str, pd.DataFrame]:
    return {
        "volume_30min": read_postgres("volume_30min"),
        "forecasting_input": read_postgres("forecasting_input"),
        "agent_performance": read_postgres("agent_performance"),
        "agent_dimension": read_postgres("agent_dimension"),
    }


def load_csv_data() -> dict[str, pd.DataFrame]:
    calls = read_csv(DATA_DIR / "synthetic_calls_sample.csv")
    forecasting = read_csv(DATA_DIR / "forecasting_input_sample.csv")
    baseline = read_csv(DATA_DIR / "baseline_forecast_sample.csv")

    if not calls.empty:
        calls["call_start_datetime"] = pd.to_datetime(calls["call_start_datetime"])
        calls["calendar_date"] = calls["call_start_datetime"].dt.date
        calls["time_id"] = calls["call_start_datetime"].dt.strftime("%H%M").astype(int)
        calls["interval_start_datetime"] = calls["call_start_datetime"].dt.floor("30min")

    return {
        "calls": calls,
        "forecasting_input": forecasting,
        "baseline": baseline,
    }


def normalize_sql_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    volume = data["volume_30min"].copy()
    forecasting = data["forecasting_input"].copy()
    agents = data["agent_performance"].copy()
    agent_dimension = data["agent_dimension"].copy()

    if not volume.empty:
        volume.columns = [column.lower() for column in volume.columns]
        volume["calendar_date"] = pd.to_datetime(volume["calendar_date"]).dt.date
        volume["offered_calls"] = pd.to_numeric(volume["offered_calls"])
        volume["answered_calls"] = pd.to_numeric(volume["answered_calls"])
        volume["abandoned_calls"] = pd.to_numeric(volume["abandoned_calls"])
        volume["avg_handle_time_sec"] = pd.to_numeric(volume["avg_handle_time_sec"])
        volume["service_level_rate"] = pd.to_numeric(volume["service_level_rate"])

    if not forecasting.empty:
        forecasting.columns = [column.lower() for column in forecasting.columns]
        forecasting["interval_start_datetime"] = pd.to_datetime(forecasting["interval_start_datetime"])
        forecasting["call_volume"] = pd.to_numeric(forecasting["call_volume"])
        forecasting["avg_handle_time_sec"] = pd.to_numeric(forecasting["avg_handle_time_sec"])

    if not agents.empty:
        agents.columns = [column.lower() for column in agents.columns]
        agents["calendar_date"] = pd.to_datetime(agents["calendar_date"]).dt.date
        agents["handled_calls"] = pd.to_numeric(agents["handled_calls"])
        agents["avg_handle_time_sec"] = pd.to_numeric(agents["avg_handle_time_sec"])
        agents["avg_talk_time_sec"] = pd.to_numeric(agents["avg_talk_time_sec"])
        agents["avg_acw_time_sec"] = pd.to_numeric(agents["avg_acw_time_sec"])

    if not agent_dimension.empty:
        agent_dimension.columns = [column.lower() for column in agent_dimension.columns]
        agent_dimension["agent_id"] = pd.to_numeric(agent_dimension["agent_id"])
        agent_dimension["active_flag"] = pd.to_numeric(agent_dimension["active_flag"])

    return {
        "volume_30min": volume,
        "forecasting_input": forecasting,
        "agent_performance": agents,
        "agent_dimension": agent_dimension,
    }


def normalize_dashboard_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return normalize_sql_data(data)


def csv_to_volume(calls: pd.DataFrame) -> pd.DataFrame:
    if calls.empty:
        return pd.DataFrame()
    grouped = (
        calls.groupby(["calendar_date", "time_id", "service_category"], as_index=False)
        .agg(
            offered_calls=("call_id", "count"),
            answered_calls=("abandoned_flag", lambda value: int((value == 0).sum())),
            abandoned_calls=("abandoned_flag", lambda value: int((value == 1).sum())),
            avg_handle_time_sec=("handle_time_sec", lambda value: value[value > 0].mean()),
            service_level_rate=("sla_met_flag", "mean"),
        )
    )
    grouped["avg_handle_time_sec"] = grouped["avg_handle_time_sec"].fillna(0)
    return grouped


def csv_to_agent_performance(calls: pd.DataFrame) -> pd.DataFrame:
    if calls.empty:
        return pd.DataFrame()
    answered = calls[(calls["abandoned_flag"] == 0) & calls["agent_id"].notna()].copy()
    if answered.empty:
        return pd.DataFrame()
    answered["agent_id"] = answered["agent_id"].astype(int)
    return (
        answered.groupby(["agent_id", "calendar_date"], as_index=False)
        .agg(
            handled_calls=("call_id", "count"),
            avg_handle_time_sec=("handle_time_sec", "mean"),
            avg_talk_time_sec=("talk_time_sec", "mean"),
            avg_acw_time_sec=("acw_time_sec", "mean"),
        )
        .sort_values("handled_calls", ascending=False)
    )


def load_data() -> tuple[str, dict[str, pd.DataFrame]]:
    source_mode = dashboard_source_mode()
    if source_mode == "postgres":
        postgres_data = normalize_dashboard_data(load_postgres_data())
        if not postgres_data["volume_30min"].empty:
            return "Postgres", postgres_data

    if source_mode != "csv":
        sql_data = normalize_sql_data(load_sql_data())
        if not sql_data["volume_30min"].empty:
            return "SQL Server", sql_data

    csv_data = load_csv_data()
    calls = csv_data["calls"]
    source = "CSV sample" if source_mode == "csv" else "CSV sample (SQL unavailable)"
    return (
        source,
        {
            "volume_30min": csv_to_volume(calls),
            "forecasting_input": csv_data["forecasting_input"],
            "agent_performance": csv_to_agent_performance(calls),
            "agent_dimension": pd.DataFrame(),
            "baseline": csv_data["baseline"],
        },
    )


def format_number(value: float, digits: int = 0) -> str:
    if pd.isna(value):
        return "0"
    if digits:
        return f"{value:,.{digits}f}"
    return f"{value:,.0f}"


def format_compact_number(value: float) -> str:
    if pd.isna(value):
        return "0"
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def format_month_year(value: Any) -> str:
    date_value = pd.to_datetime(value)
    return date_value.strftime("%b %Y")


def render_plotly_chart(fig: Any) -> None:
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def render_dataframe(data: pd.DataFrame, **kwargs: Any) -> None:
    try:
        st.dataframe(data, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(data, use_container_width=True, **kwargs)


def render_chapter_header(kicker: str, title: str, deck: str, tag: str = "") -> None:
    tag_html = f'<div class="chapter-tag">{escape(tag)}</div>' if tag else ""
    st.markdown(
        f"""
        <div class="chapter-header">
            <div class="chapter-kicker">{escape(kicker)}</div>
            <div class="chapter-title">{escape(title)}</div>
            <div class="chapter-dek">{escape(deck)}</div>
            {tag_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_strip(metrics: list[tuple[str, str, str]]) -> None:
    cards = []
    for label, value, note in metrics:
        cards.append(
            '<div class="editorial-metric">'
            f'<div class="editorial-metric-label">{escape(label)}</div>'
            f'<div class="editorial-metric-value">{escape(str(value))}</div>'
            f'<div class="editorial-metric-note">{escape(note)}</div>'
            "</div>"
        )
    st.markdown(
        f'<div class="editorial-metric-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_section_header(label: str, note: str = "") -> None:
    note_html = f'<div class="editorial-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f"""
        <div class="editorial-section">{escape(label)}</div>
        {note_html}
        """,
        unsafe_allow_html=True,
    )


def render_chart_header(label: str, note: str = "") -> None:
    note_html = f'<div class="chart-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f"""
        <div class="chart-label">{escape(label)}</div>
        {note_html}
        """,
        unsafe_allow_html=True,
    )


def style_editorial_figure(fig: Any, height: int | None = None) -> Any:
    layout_updates: dict[str, Any] = {
        "paper_bgcolor": PANEL_BG,
        "plot_bgcolor": PANEL_BG,
        "colorway": EDITORIAL_COLORS,
        "font": {"family": "Arial, sans-serif", "color": INK},
        "title_text": "",
        "title_font": {"family": "Arial, sans-serif", "size": 12, "color": MUTED},
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.22,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11, "color": MUTED},
        },
        "margin": {"l": 32, "r": 24, "t": 82, "b": 48},
    }
    if height:
        layout_updates["height"] = height
    fig.update_layout(**layout_updates)
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor=RULE,
        zeroline=False,
        tickfont={"size": 11, "color": MUTED},
        title_font={"size": 12, "color": MUTED},
    )
    fig.update_yaxes(
        gridcolor=GRID,
        showline=False,
        zeroline=False,
        tickfont={"size": 11, "color": MUTED},
        title_font={"size": 12, "color": MUTED},
    )
    return fig


def add_chart_source(fig: Any, text: str) -> Any:
    style_editorial_figure(fig)
    fig.update_layout(title_text="")
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=0,
        y=1.08,
        showarrow=False,
        align="left",
        font={"size": 11, "color": "#6b7280"},
    )
    margin = getattr(fig.layout, "margin", None)
    top_margin = margin.t if margin and margin.t is not None else 60
    fig.update_layout(margin={"t": max(top_margin, 82)})
    return fig


def render_insight_callout(text: str) -> None:
    st.markdown(
        f'<div class="insight-callout"><span class="callout-label">Interpretation</span>{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def apply_agent_name_lookup(frame: pd.DataFrame, lookup: dict[int, str]) -> pd.DataFrame:
    if frame.empty or "agent_id" not in frame.columns or not lookup:
        return frame
    updated = frame.copy()
    updated["agent_id"] = pd.to_numeric(updated["agent_id"])
    updated["agent_name"] = updated["agent_id"].map(lookup).fillna(updated.get("agent_name", ""))
    return updated


def render_sidebar(source: str, volume: pd.DataFrame) -> tuple[list[str], tuple[Any, Any]]:
    source_label = escape(
        {
            "Postgres": "CURATED DEMO",
            "SQL Server": "Local warehouse",
            "CSV sample": "Sample evidence",
            "CSV sample (SQL unavailable)": "Sample evidence",
        }.get(source, "CURATED DEMO")
    )
    st.sidebar.markdown(
        f"""
        <div class="sidebar-masthead">
            <div class="sidebar-title">Call Center WFM</div>
            <div class="sidebar-summary">
                A portfolio case study based on NYC 311 demand, from historical volume through forecasting,
                staffing, roster simulation, and modeled service outcomes.
            </div>
            <div class="sidebar-source">
                <span class="sidebar-source-label">Evidence mode</span>
                <span class="sidebar-source-pill">{source_label}</span>
            </div>
        </div>
        <div class="sidebar-card">
            <div class="sidebar-card-label">Reader Guide</div>
            <div class="sidebar-card-title">Demand, forecast, staffing, roster</div>
            <div class="sidebar-card-text">
                Read the tabs as a sequence. The filters narrow the view without changing the underlying method.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar.expander("Transparency Ledger", expanded=True):
        st.markdown(
            """
            <div class="sidebar-ledger">
                <div class="sidebar-ledger-row">
                    <span class="sidebar-ledger-label real">REAL</span>
                    NYC 311 request timestamps and volumes.
                </div>
                <div class="sidebar-ledger-row">
                    <span class="sidebar-ledger-label synthetic">SYNTHETIC</span>
                    AHT, abandonment, SLA targets, and agent records.
                </div>
                <div class="sidebar-ledger-row">
                    <span class="sidebar-ledger-label forecasted">FORECASTED</span>
                    Model outputs for future demand intervals.
                </div>
                <div class="sidebar-ledger-row">
                    <span class="sidebar-ledger-label simulated">SIMULATED</span>
                    Staffing plans, roster assignments, and service outcomes.
                </div>
                <div class="sidebar-ledger-note">
                    Built for analytical demonstration, not live operations software.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.markdown('<div class="sidebar-filter-label">Filters</div>', unsafe_allow_html=True)
    service_categories = sorted(volume["service_category"].dropna().unique()) if not volume.empty else []
    selected_categories = st.sidebar.multiselect(
        "Service categories",
        options=service_categories,
        default=service_categories,
    )

    if not volume.empty:
        dates = sorted(volume["calendar_date"].dropna().unique())
        selected_dates = st.sidebar.date_input(
            "Date range",
            value=(dates[0], dates[-1]),
            min_value=dates[0],
            max_value=dates[-1],
        )
        if len(selected_dates) == 1:
            selected_dates = (selected_dates[0], selected_dates[0])
    else:
        selected_dates = (None, None)

    return selected_categories, selected_dates


def apply_filters(
    volume: pd.DataFrame,
    categories: list[str],
    date_range: tuple[Any, Any],
) -> pd.DataFrame:
    if volume.empty:
        return volume
    filtered = volume.copy()
    if categories:
        filtered = filtered[filtered["service_category"].isin(categories)]
    start, end = date_range
    if start and end:
        filtered = filtered[
            (pd.to_datetime(filtered["calendar_date"]) >= pd.to_datetime(start))
            & (pd.to_datetime(filtered["calendar_date"]) <= pd.to_datetime(end))
        ]
    return filtered


def render_executive_summary(volume: pd.DataFrame) -> None:
    if volume.empty:
        st.info("Historical call volume data is not available.")
        return

    total_calls = volume["offered_calls"].sum() if not volume.empty else 0
    service_level = (
        (volume["service_level_rate"] * volume["offered_calls"]).sum() / total_calls
        if total_calls
        else 0
    )
    period_start = pd.to_datetime(volume["calendar_date"]).min()
    period_end = pd.to_datetime(volume["calendar_date"]).max()
    coverage_months = (
        (period_end.year - period_start.year) * 12 + period_end.month - period_start.month + 1
        if pd.notna(period_start) and pd.notna(period_end)
        else 0
    )

    monthly = (
        volume.assign(month=pd.to_datetime(volume["calendar_date"]).dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .agg(
            offered_calls=("offered_calls", "sum"),
            answered_calls=("answered_calls", "sum"),
            abandoned_calls=("abandoned_calls", "sum"),
        )
        .sort_values("month")
    )
    category = (
        volume.groupby("service_category", as_index=False)
        .agg(offered_calls=("offered_calls", "sum"))
        .sort_values("offered_calls", ascending=False)
    )
    top_category = category.iloc[0]["service_category"] if not category.empty else "selected services"
    yoy_note = "Monthly request volume varies across the selected demand window."
    if len(monthly) >= 14:
        latest_month = monthly.iloc[-1]
        prior_year_month = latest_month["month"] - pd.DateOffset(years=1)
        prior = monthly[monthly["month"] == prior_year_month]
        if not prior.empty and prior.iloc[0]["offered_calls"]:
            yoy_change = (
                latest_month["offered_calls"] - prior.iloc[0]["offered_calls"]
            ) / prior.iloc[0]["offered_calls"]
            direction = "up" if yoy_change >= 0 else "down"
            yoy_note = f"Latest comparable month is {direction} {abs(yoy_change):.1%} year over year."

    st.markdown('<div class="portfolio-overview">', unsafe_allow_html=True)
    header_left, header_right = st.columns([3.8, 1.2])
    with header_left:
        st.markdown(
            """
            <div class="portfolio-eyebrow">Workforce Management · Portfolio Project</div>
            <div class="portfolio-title">NYC 311 Call Center<br>WFM Analytics Prototype</div>
            <div class="portfolio-dek">
            This page summarizes the scale of historical NYC 311 demand and shows how the prototype separates
            real data from forecasted, synthetic, and simulated layers.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_right:
        st.markdown(
            f"""
            <div class="portfolio-meta">
                <div class="portfolio-smallcaps">Data Period</div>
                <div class="portfolio-meta-value">{format_month_year(period_start)} - {format_month_year(period_end)}</div>
                <div class="portfolio-meta-note">Source: NYC Open Data · real demand</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="portfolio-rule">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="portfolio-kpi-grid">
            <div class="portfolio-kpi">
                <div class="portfolio-kpi-label">Service<br>Requests</div>
                <div class="portfolio-kpi-value">{format_compact_number(total_calls)}</div>
                <div class="portfolio-kpi-note">real NYC 311 demand</div>
            </div>
            <div class="portfolio-kpi">
                <div class="portfolio-kpi-label">Coverage<br>Period</div>
                <div class="portfolio-kpi-value">{coverage_months}<span style="font-size:1rem;"> mo</span></div>
                <div class="portfolio-kpi-note">observed demand window</div>
            </div>
            <div class="portfolio-kpi">
                <div class="portfolio-kpi-label">Simulated<br>Agents</div>
                <div class="portfolio-kpi-value">160</div>
                <div class="portfolio-kpi-note">fixed roster constraint</div>
            </div>
            <div class="portfolio-kpi">
                <div class="portfolio-kpi-label">SLA<br>Compliance</div>
                <div class="portfolio-kpi-value">{service_level:.1%}</div>
                <div class="portfolio-kpi-note">modeled under 160-agent constraint</div>
            </div>
            <div class="portfolio-kpi">
                <div class="portfolio-kpi-label">Forecast<br>Interval</div>
                <div class="portfolio-kpi-value">30<span style="font-size:1rem;"> min</span></div>
                <div class="portfolio-kpi-note">forecast grain</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown(
            f"""
            <div class="portfolio-section-label">Monthly Service Request Volume · NYC 311</div>
            <div class="portfolio-section-copy">
            {escape(yoy_note)} {escape(str(top_category)).title()} is the largest selected category,
            giving the prototype a high-volume demand base across the full observation window.
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly["offered_calls"],
                mode="lines",
                line={"color": "#24364b", "width": 2.2},
                fill="tozeroy",
                fillcolor="rgba(47, 111, 159, 0.14)",
                hovertemplate="%{x|%b %Y}<br>%{y:,.0f} requests<extra></extra>",
                name="Service requests",
            )
        )
        if not monthly.empty:
            peak = monthly.loc[monthly["offered_calls"].idxmax()]
            latest = monthly.iloc[-1]
            fig.add_annotation(
                x=peak["month"],
                y=peak["offered_calls"],
                text=f"Peak<br>{format_compact_number(peak['offered_calls'])}",
                showarrow=True,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor="#7c6f60",
                ax=38,
                ay=-44,
                bgcolor="rgba(248, 243, 234, 0.92)",
                bordercolor="#cbbfac",
                borderwidth=1,
                font={"color": "#2b3444", "size": 11},
            )
            fig.add_annotation(
                x=latest["month"],
                y=latest["offered_calls"],
                text=f"Latest<br>{format_compact_number(latest['offered_calls'])}",
                showarrow=True,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor="#7c6f60",
                ax=-58,
                ay=-18,
                bgcolor="rgba(248, 243, 234, 0.92)",
                bordercolor="#cbbfac",
                borderwidth=1,
                font={"color": "#2b3444", "size": 11},
            )
        fig.update_layout(
            height=390,
            margin={"l": 8, "r": 8, "t": 18, "b": 28},
            paper_bgcolor="#f8f3ea",
            plot_bgcolor="#f8f3ea",
            font={"family": "Arial, sans-serif", "color": "#2d3340"},
            xaxis={
                "showgrid": False,
                "showline": True,
                "linecolor": "#cfc5b7",
                "tickfont": {"size": 11, "color": "#5e5a52"},
            },
            yaxis={
                "title": None,
                "gridcolor": "#e2d8ca",
                "zeroline": False,
                "tickformat": "~s",
                "tickfont": {"size": 11, "color": "#5e5a52"},
            },
            showlegend=False,
        )
        render_plotly_chart(fig)
        st.caption(
            "Source: NYC 311 Service Requests, NYC Open Data. Values shown as monthly request totals. Real data."
        )
    with right:
        st.markdown(
            """
            <div class="portfolio-section-label">Analytical Pipeline</div>
            <div class="portfolio-pipeline">
                <div class="portfolio-pipeline-step">
                    <div class="portfolio-step-row">
                        <div>
                            <div class="portfolio-step-title">NYC 311 open data</div>
                            <div class="portfolio-step-note">Public request timestamps and categories</div>
                        </div>
                        <span class="portfolio-chip real">Real</span>
                    </div>
                </div>
                <div class="portfolio-pipeline-step synthetic">
                    <div class="portfolio-step-row">
                        <div>
                            <div class="portfolio-step-title">Synthetic metadata overlay</div>
                            <div class="portfolio-step-note">AHT, hold time, SLA, and agent IDs</div>
                        </div>
                        <span class="portfolio-chip synthetic">Synthetic</span>
                    </div>
                </div>
                <div class="portfolio-pipeline-step forecasted">
                    <div class="portfolio-step-row">
                        <div>
                            <div class="portfolio-step-title">ML demand forecast</div>
                            <div class="portfolio-step-note">Future 30-minute demand intervals</div>
                        </div>
                        <span class="portfolio-chip forecasted">Forecasted</span>
                    </div>
                </div>
                <div class="portfolio-pipeline-step simulated">
                    <div class="portfolio-step-row">
                        <div>
                            <div class="portfolio-step-title">Erlang C and roster simulation</div>
                            <div class="portfolio-step-note">Required agents and shift coverage</div>
                        </div>
                        <span class="portfolio-chip simulated">Simulated</span>
                    </div>
                </div>
            </div>
            <div class="portfolio-transparency">
                <div class="portfolio-section-label">Data Transparency</div>
                Demand data is real and public. Everything after the demand layer is documented
                as synthetic, forecasted, or simulated.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_historical_trends(volume: pd.DataFrame) -> None:
    if volume.empty:
        st.info("Historical trend data is not available.")
        return

    render_chapter_header(
        "CHAPTER 02 · DEMAND ANALYSIS",
        "Demand by Hour and Weekday",
        (
            "This page shows how demand is distributed across the week and identifies the recurring "
            "periods with the highest average call volume."
        ),
        "REAL NYC 311 DEMAND",
    )

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap = volume.copy()
    heatmap["calendar_date_dt"] = pd.to_datetime(heatmap["calendar_date"])
    heatmap["day_name"] = heatmap["calendar_date_dt"].dt.day_name()
    heatmap["hour"] = heatmap["time_id"].astype(str).str.zfill(4).str[:2].astype(int)
    heatmap["hour_label"] = heatmap["hour"].map(lambda value: f"{value:02d}:00")
    date_hour = (
        heatmap.groupby(["calendar_date", "day_name", "hour_label"], as_index=False)
        .agg(offered_calls=("offered_calls", "sum"))
    )
    day_hour = (
        date_hour.groupby(["day_name", "hour_label"], as_index=False)
        .agg(avg_calls=("offered_calls", "mean"))
    )
    day_hour["day_name"] = pd.Categorical(day_hour["day_name"], categories=day_order, ordered=True)
    day_hour = day_hour.sort_values(["day_name", "hour_label"])
    pivot = day_hour.pivot(index="day_name", columns="hour_label", values="avg_calls").fillna(0)
    peak_hour = day_hour.loc[day_hour["avg_calls"].idxmax()]
    rendered_days = volume["calendar_date"].nunique()

    render_insight_callout(
        (
            "Demand is concentrated by hour and weekday, not evenly distributed. "
            f"The highest average load occurs on {peak_hour['day_name']} at {peak_hour['hour_label']}, "
            "which supports interval-based forecasting."
        )
    )

    render_metric_strip(
        [
            ("Observed Days", format_number(rendered_days), "days in view"),
            ("Peak Day", str(peak_hour["day_name"]), "highest hourly average"),
            ("Peak Hour", str(peak_hour["hour_label"]), "highest average hour"),
            ("Peak Avg Calls", format_number(peak_hour["avg_calls"], 1), "average calls at peak"),
        ]
    )
    render_chart_header(
        "Intraday Demand Heatmap",
        (
            "The heatmap shows average offered calls by hour and weekday across the selected demand window. "
            "Darker cells indicate recurring periods of higher demand."
        ),
    )

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale=["#f8f3ea", "#d7e6ed", "#6da3c8", "#2f6f9f", "#16324a"],
        labels={"color": "Avg calls"},
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        coloraxis_colorbar={"title": "Avg calls"},
        height=460,
    )
    fig.add_annotation(
        x=str(peak_hour["hour_label"]),
        y=str(peak_hour["day_name"]),
        text=f"Peak<br>{format_number(peak_hour['avg_calls'], 1)}",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1,
        arrowcolor="#7c6f60",
        ax=36,
        ay=-30,
        bgcolor="rgba(248, 243, 234, 0.92)",
        bordercolor="#cbbfac",
        borderwidth=1,
        font={"color": INK, "size": 11},
    )
    add_chart_source(fig, "Source: REAL NYC 311 demand")
    render_plotly_chart(fig)
    st.caption("Values are average offered calls by hour and weekday for the selected demand window.")


def render_forecasting(forecasting: pd.DataFrame) -> None:
    summary = load_first_json(
        [
            DOCS_DIR / "full_baseline_forecast_summary.json",
            DOCS_DIR / "baseline_forecast_summary.json",
        ]
    )
    model_summary = load_first_json(
        [
            DOCS_DIR / "full_sklearn_model_comparison_summary.json",
            DOCS_DIR / "sklearn_model_comparison_summary.json",
        ]
    )
    future_summary = load_first_json([DOCS_DIR / "future_forecast_summary.json"])

    render_chapter_header(
        "CHAPTER 03 · FORECAST EVIDENCE",
        "Forecast Model Comparison and Planning Output",
        (
            "This page compares forecast models on holdout data and then shows the selected forecast "
            "horizon used in downstream staffing and roster simulation."
        ),
        "FORECASTED MODEL OUTPUT",
    )
    render_insight_callout(
        (
            "Histogram Gradient Boosting demonstrates the highest performance, followed by Random Forest, "
            "while the other three models perform significantly worse. This ranking remains consistent "
            "across all reported error metrics, with the greatest difference observed in RMSE."
        )
    )

    render_metric_strip(
        [
            ("Test Intervals", format_number(summary.get("test_intervals", 0)), "holdout evidence"),
            ("MAE", format_number(summary.get("mae", 0), 2), "typical miss"),
            ("RMSE", format_number(summary.get("rmse", 0), 2), "peak-sensitive miss"),
            ("MAPE", f"{summary.get('mape', 0):.1%}", "relative miss rate"),
        ]
    )

    model_rows = pd.DataFrame(model_summary.get("models", [])) if model_summary else pd.DataFrame()
    model_names = model_rows["model"].tolist() if not model_rows.empty else []
    selected_model = model_summary.get("selected_model", "") if model_summary else ""

    if not model_rows.empty:
        render_section_header(
            "Model Comparison",
            (
                "Histogram Gradient Boosting demonstrates the highest performance, followed by Random Forest, "
                "while the other three models perform significantly worse. This ranking remains consistent "
                "across all reported error metrics, with the greatest difference observed in RMSE."
            ),
        )
        display_rows = model_rows.copy()
        display_rows["model"] = display_rows["model"].map(model_label)
        render_dataframe(display_rows, hide_index=True)

    baseline = read_postgres_or_first_csv(
        "baseline_forecast",
        [
            DATA_DIR / "full_baseline_forecast.csv",
            DATA_DIR / "baseline_forecast_sample.csv",
        ]
    )
    feature_forecast = read_postgres_or_first_csv(
        "feature_forecast",
        [
            DATA_DIR / "full_sklearn_best_forecast.csv",
            DATA_DIR / "sklearn_best_forecast_sample.csv",
        ]
    )
    future_forecast = read_postgres_or_first_csv(
        "future_forecast",
        [DATA_DIR / "future_sklearn_forecast.csv"],
    )
    model_predictions = read_postgres_or_first_csv(
        "model_holdout_predictions",
        [
            DATA_DIR / "full_model_holdout_predictions.csv",
            DATA_DIR / "model_holdout_predictions.csv",
            DATA_DIR / "sklearn_model_holdout_predictions_sample.csv",
        ]
    )
    future_model_scenarios = read_postgres_or_first_csv(
        "future_model_scenarios",
        [DATA_DIR / "future_model_scenario_forecasts.csv"],
    )
    if baseline.empty:
        st.info("Baseline forecast output is not available.")
        return

    baseline["interval_start_datetime"] = pd.to_datetime(baseline["interval_start_datetime"])
    baseline["actual_call_volume"] = pd.to_numeric(baseline["actual_call_volume"])
    baseline["predicted_call_volume"] = pd.to_numeric(baseline["predicted_call_volume"])
    if not feature_forecast.empty:
        feature_forecast["interval_start_datetime"] = pd.to_datetime(feature_forecast["interval_start_datetime"])
        feature_forecast["predicted_call_volume"] = pd.to_numeric(feature_forecast["predicted_call_volume"])
        if "actual_call_volume" in feature_forecast.columns:
            feature_forecast["actual_call_volume"] = pd.to_numeric(feature_forecast["actual_call_volume"])

    if not model_predictions.empty:
        model_predictions["interval_start_datetime"] = pd.to_datetime(
            model_predictions["interval_start_datetime"]
        )
        model_predictions["actual_call_volume"] = pd.to_numeric(
            model_predictions["actual_call_volume"]
        )
        model_predictions["predicted_call_volume"] = pd.to_numeric(
            model_predictions["predicted_call_volume"]
        )
        available_models = model_predictions["model"].dropna().unique().tolist()
        default_models = unique_values([
            model for model in [selected_model, "random_forest", "gradient_boosting"] if model in available_models
        ])
        selected_models = st.multiselect(
            "Holdout models",
            options=available_models,
            default=default_models or available_models[: min(3, len(available_models))],
            format_func=model_label,
        )
    else:
        selected_models = []

    render_chart_header(
        "Holdout Forecast Evidence",
        (
            "The chart compares actual historical demand with candidate model outputs over the same holdout "
            "window, allowing forecast error to be evaluated directly against observed volume."
        ),
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=baseline["interval_start_datetime"],
            y=baseline["actual_call_volume"],
            mode="lines",
            name="Actual",
            line={"color": ACCENT_DARK, "width": 2.2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=baseline["interval_start_datetime"],
            y=baseline["predicted_call_volume"],
            mode="lines",
            name="Baseline",
            line={"color": "#8c867c", "width": 1.5, "dash": "dot"},
        )
    )
    if selected_models and not model_predictions.empty:
        for index, model in enumerate(selected_models):
            model_slice = model_predictions[model_predictions["model"] == model]
            fig.add_trace(
                go.Scatter(
                    x=model_slice["interval_start_datetime"],
                    y=model_slice["predicted_call_volume"],
                    mode="lines",
                    name=model_label(model),
                    line={"color": EDITORIAL_COLORS[(index + 1) % len(EDITORIAL_COLORS)], "width": 1.7},
                )
            )
    elif not feature_forecast.empty:
        fig.add_trace(
            go.Scatter(
                x=feature_forecast["interval_start_datetime"],
                y=feature_forecast["predicted_call_volume"],
                mode="lines",
                name=f"Best feature model ({model_label(selected_model or 'selected')})",
                line={"color": ACCENT, "width": 1.8},
            )
        )
    fig.update_layout(title="Forecast holdout period", xaxis_title=None, yaxis_title="Calls")
    add_chart_source(fig, "REAL historical demand + FORECASTED model output")
    render_plotly_chart(fig)

    if not model_rows.empty:
        error_rows = model_rows.melt(
            id_vars="model",
            value_vars=[column for column in ["mae", "rmse", "mape"] if column in model_rows.columns],
            var_name="metric",
            value_name="value",
        )
        error_rows["model"] = error_rows["model"].map(model_label)
        render_chart_header(
            "Validation Error by Model",
            (
                "Performance differences remain consistent across all reported error metrics. Histogram "
                "Gradient Boosting and Random Forest achieve the lowest errors, while Ridge and Poisson "
                "record the highest, with the clearest separation observed in RMSE."
            ),
        )
        fig = px.bar(
            error_rows,
            x="model",
            y="value",
            color="metric",
            barmode="group",
            color_discrete_sequence=[ACCENT_DARK, ACCENT, ACCENT_WARM],
        )
        fig.update_layout(title="Holdout error by model", xaxis_title=None, yaxis_title="Error")
        add_chart_source(fig, "FORECASTED validation output")
        render_plotly_chart(fig)

    if not future_forecast.empty:
        future_forecast["interval_start_datetime"] = pd.to_datetime(
            future_forecast["interval_start_datetime"]
        )
        future_forecast["predicted_call_volume"] = pd.to_numeric(
            future_forecast["predicted_call_volume"]
        )
        render_section_header(
            "Future Planning Forecast",
            (
                "This section shows the forecast horizon used as the input for staffing and roster simulation. "
                "The values below summarize the modeled 30-minute demand profile for the selected planning period."
            ),
        )
        render_metric_strip(
            [
                ("Forecast Intervals", format_number(future_summary.get("forecast_intervals", len(future_forecast))), "30-minute horizon"),
                ("Forecast Start", str(future_summary.get("forecast_start", "")), "first modeled interval"),
                ("Avg Calls", format_number(future_summary.get("avg_predicted_calls", 0), 1), "expected interval load"),
                ("Peak Calls", format_number(future_summary.get("peak_predicted_calls", 0), 1), "planning peak"),
            ]
        )
        if not future_model_scenarios.empty:
            future_model_scenarios["interval_start_datetime"] = pd.to_datetime(
                future_model_scenarios["interval_start_datetime"]
            )
            future_model_scenarios["predicted_call_volume"] = pd.to_numeric(
                future_model_scenarios["predicted_call_volume"]
            )
            scenario_models = future_model_scenarios["model"].dropna().unique().tolist()
            scenario_default = unique_values([
                model for model in [future_summary.get("selected_model", selected_model), "random_forest"] if model in scenario_models
            ])
            selected_scenarios = st.multiselect(
                "Future planning models",
                options=scenario_models,
                default=scenario_default or scenario_models[: min(2, len(scenario_models))],
                format_func=model_label,
            )
            scenario_plot = future_model_scenarios[
                future_model_scenarios["model"].isin(selected_scenarios)
            ].copy()
            scenario_plot["model"] = scenario_plot["model"].map(model_label)
            fig = px.line(
                scenario_plot,
                x="interval_start_datetime",
                y="predicted_call_volume",
                color="model",
                color_discrete_sequence=EDITORIAL_COLORS,
            )
            summary_by_model = (
                future_model_scenarios.groupby("model", as_index=False)
                .agg(
                    avg_calls=("predicted_call_volume", "mean"),
                    peak_calls=("predicted_call_volume", "max"),
                )
                .sort_values("avg_calls", ascending=False)
            )
            summary_by_model["model"] = summary_by_model["model"].map(model_label)
            render_dataframe(summary_by_model, hide_index=True)
        else:
            fig = px.line(
                future_forecast,
                x="interval_start_datetime",
                y="predicted_call_volume",
            )
        render_chart_header(
            "Forecasted Model Output",
            "The line chart shows the modeled call volume pattern across the planning horizon for the selected forecast models.",
        )
        fig.update_layout(title="Future 30-minute call forecast", xaxis_title=None, yaxis_title="Calls")
        add_chart_source(fig, "FORECASTED model output")
        render_plotly_chart(fig)

    if not forecasting.empty:
        render_section_header(
            "Forecasting Input Mix",
            (
                "The historical category mix used for forecasting is shown below. Housing carries the largest "
                "share of demand, followed by general and transportation."
            ),
        )
        top = (
            forecasting.groupby("service_category", as_index=False)
            .agg(call_volume=("call_volume", "sum"))
            .sort_values("call_volume", ascending=False)
        )
        fig = px.bar(top, x="service_category", y="call_volume", color_discrete_sequence=[ACCENT])
        fig.update_layout(title="Forecasting input by category", xaxis_title=None, yaxis_title="Calls")
        add_chart_source(fig, "Source: REAL NYC 311 demand")
        render_plotly_chart(fig)


def render_staffing() -> None:
    summary = load_first_json(
        [
            DOCS_DIR / "future_staffing_requirements_summary.json",
            DOCS_DIR / "full_staffing_requirements_summary.json",
            DOCS_DIR / "staffing_requirements_summary.json",
        ]
    )
    staffing = read_postgres_or_first_csv(
        "staffing_requirements",
        [
            DATA_DIR / "future_staffing_requirements.csv",
            DATA_DIR / "full_staffing_requirements.csv",
            DATA_DIR / "staffing_requirements_sample.csv",
        ]
    )
    if staffing.empty:
        st.info("Staffing requirements output is not available.")
        return
    scenario_summary = load_json(DOCS_DIR / "future_model_staffing_scenario_summary.json")
    staffing["interval_start_datetime"] = pd.to_datetime(staffing["interval_start_datetime"])
    staffing["predicted_call_volume"] = pd.to_numeric(staffing["predicted_call_volume"])
    staffing["base_required_agents"] = pd.to_numeric(staffing["base_required_agents"])
    staffing["shrinkage_adjusted_agents"] = pd.to_numeric(staffing["shrinkage_adjusted_agents"])
    staffing["expected_occupancy"] = pd.to_numeric(staffing["expected_occupancy"])
    staffing["service_level_probability"] = pd.to_numeric(staffing["service_level_probability"])

    render_chapter_header(
        "CHAPTER 04 · CAPACITY PLANNING",
        "Forecasted Volume and Required Staffing",
        "This page shows how forecasted 30-minute call volume converts into required staffing under the selected queueing assumptions.",
        "FORECASTED + SIMULATED",
    )
    render_insight_callout(
        (
            f"Across {format_number(summary.get('interval_count', len(staffing)))} forecast intervals, "
            f"peak base staffing reaches {format_number(summary.get('peak_base_required_agents', 0))} agents and "
            f"peak shrinkage-adjusted staffing reaches {format_number(summary.get('peak_shrinkage_adjusted_agents', 0))}. "
            "The staffing requirement follows the same daily pattern as demand, but remains materially higher once shrinkage is applied."
        )
    )

    render_metric_strip(
        [
            ("Intervals", format_number(summary.get("interval_count", len(staffing))), "30-min periods"),
            ("Peak Base FTE", format_number(summary.get("peak_base_required_agents", 0)), "before shrinkage"),
            ("Peak Shrinkage FTE", format_number(summary.get("peak_shrinkage_adjusted_agents", 0)), "including shrinkage"),
            ("Avg Service Level", f"{summary.get('avg_service_level_probability', 0):.1%}", "modeled result"),
        ]
    )

    render_section_header(
        "Staffing Requirement Curve",
        (
            "The chart compares forecasted call volume with required staffing for each 30-minute interval. "
            "The gap between base and shrinkage-adjusted staffing represents the additional staffing needed beyond raw queue demand."
        ),
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=staffing["interval_start_datetime"],
            y=staffing["base_required_agents"],
            mode="lines",
            name="Base required agents",
            line={"color": ACCENT_DARK, "width": 1.9},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=staffing["interval_start_datetime"],
            y=staffing["shrinkage_adjusted_agents"],
            mode="lines",
            name="Shrinkage-adjusted agents",
            line={"color": ACCENT, "width": 2.1},
        )
    )
    fig.add_trace(
        go.Bar(
            x=staffing["interval_start_datetime"],
            y=staffing["predicted_call_volume"],
            name="Predicted calls",
            yaxis="y2",
            opacity=0.28,
            marker={"color": "#d9766a"},
        )
    )
    peak_staffing = staffing.loc[staffing["shrinkage_adjusted_agents"].idxmax()]
    fig.add_annotation(
        x=peak_staffing["interval_start_datetime"],
        y=peak_staffing["shrinkage_adjusted_agents"],
        text=f"Peak need<br>{format_number(peak_staffing['shrinkage_adjusted_agents'])}",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1,
        arrowcolor="#7c6f60",
        ax=44,
        ay=-38,
        bgcolor="rgba(248, 243, 234, 0.92)",
        bordercolor="#cbbfac",
        borderwidth=1,
        font={"color": INK, "size": 11},
    )
    fig.update_layout(
        title="Forecasted calls and required staffing",
        xaxis_title=None,
        yaxis_title="Agents",
        yaxis2={"title": "Calls", "overlaying": "y", "side": "right"},
        legend={"orientation": "h"},
    )
    add_chart_source(fig, "FORECASTED demand + SIMULATED Erlang C staffing")
    render_plotly_chart(fig)

    scenario_rows = pd.DataFrame(scenario_summary.get("models", []))
    if not scenario_rows.empty:
        render_section_header(
            "Model Impact on Staffing",
            (
                "Different forecast models produce different call volumes, which leads to different staffing "
                "requirements. In this comparison, Random Forest produces the highest peak staffing estimate, "
                "while Ridge produces the lowest."
            ),
        )
        scenario_display = scenario_rows[
            [
                "model",
                "avg_predicted_calls",
                "peak_predicted_calls",
                "avg_shrinkage_adjusted_agents",
                "peak_shrinkage_adjusted_agents",
                "estimated_full_coverage_agents",
                "approved_agent_pool_gap",
            ]
        ].copy()
        scenario_display["model"] = scenario_display["model"].map(model_label)
        render_dataframe(scenario_display, hide_index=True)
        render_section_header(
            "Simulated Staffing Scenario Output",
            "Peak staffing requirements vary materially across models, showing that forecast selection affects downstream capacity estimates.",
        )
        scenario_plot = scenario_display.melt(
            id_vars="model",
            value_vars=["peak_shrinkage_adjusted_agents", "estimated_full_coverage_agents"],
            var_name="metric",
            value_name="agents",
        )
        fig = px.bar(
            scenario_plot,
            x="model",
            y="agents",
            color="metric",
            barmode="group",
            color_discrete_sequence=[ACCENT_DARK, ACCENT_SOFT],
        )
        fig.update_layout(title="Staffing impact by forecast model", xaxis_title=None, yaxis_title="Agents")
        add_chart_source(fig, "SIMULATED staffing scenario output")
        render_plotly_chart(fig)

    render_section_header(
        "Interval Detail Table",
        (
            "This table lists the interval-level inputs and outputs used in the staffing calculation, including "
            "predicted call volume, average handle time, traffic intensity, and required agents."
        ),
    )
    display = staffing[
        [
            "interval_start_datetime",
            "predicted_call_volume",
            "avg_handle_time_sec",
            "traffic_intensity_erlangs",
            "base_required_agents",
            "shrinkage_adjusted_agents",
            "expected_occupancy",
            "service_level_probability",
        ]
    ].copy()
    render_dataframe(display, hide_index=True)


def render_scheduling() -> None:
    summary = load_first_json(
        [
            DOCS_DIR / "future_scheduling_summary.json",
            DOCS_DIR / "full_scheduling_summary.json",
            DOCS_DIR / "scheduling_summary.json",
        ]
    )
    schedule = read_postgres_or_first_csv(
        "optimized_schedule",
        [
            DATA_DIR / "future_optimized_schedule.csv",
            DATA_DIR / "full_optimized_schedule.csv",
            DATA_DIR / "optimized_schedule_sample.csv",
        ]
    )
    coverage = read_postgres_or_first_csv(
        "schedule_coverage",
        [
            DATA_DIR / "future_schedule_coverage.csv",
            DATA_DIR / "full_schedule_coverage.csv",
            DATA_DIR / "schedule_coverage_sample.csv",
        ]
    )
    if schedule.empty or coverage.empty:
        st.info("Roster simulation output is not available.")
        return

    schedule["shift_start_datetime"] = pd.to_datetime(schedule["shift_start_datetime"])
    schedule["shift_end_datetime"] = pd.to_datetime(schedule["shift_end_datetime"])
    schedule["break_start_datetime"] = pd.to_datetime(schedule["break_start_datetime"])
    schedule["break_end_datetime"] = pd.to_datetime(schedule["break_end_datetime"])
    schedule["shift_date"] = pd.to_datetime(schedule["shift_date"]).dt.date
    coverage["interval_start_datetime"] = pd.to_datetime(coverage["interval_start_datetime"])
    coverage["required_agents"] = pd.to_numeric(coverage["required_agents"])
    coverage["scheduled_agents"] = pd.to_numeric(coverage["scheduled_agents"])
    coverage["understaffed_agents"] = pd.to_numeric(coverage["understaffed_agents"])
    coverage["overstaffed_agents"] = pd.to_numeric(coverage["overstaffed_agents"])
    coverage_achieved = summary.get("coverage_achieved_rate")
    if coverage_achieved is None:
        total_required = coverage["required_agents"].sum()
        coverage_achieved = (
            (total_required - coverage["understaffed_agents"].sum()) / total_required
            if total_required
            else 0
        )
    understaffed_intervals = int((coverage["understaffed_agents"] > 0).sum())

    render_chapter_header(
        "CHAPTER 05 · ROSTER SIMULATION",
        "Required Staffing vs Simulated Roster Coverage",
        "This page compares required staffing with the simulated roster and shows where scheduled coverage falls short across the planning horizon.",
        "SIMULATED ROSTER ALLOCATION",
    )
    render_insight_callout(
        (
            "The simulated roster does not meet modeled demand at peak periods. "
            f"With {format_number(summary.get('peak_scheduled_agents', 0))} scheduled agents against a peak requirement of "
            f"{format_number(summary.get('peak_required_agents', 0))}, coverage remains below full need across much of the planning window."
        )
    )

    render_metric_strip(
        [
            ("Shifts", format_number(summary.get("scheduled_shifts", len(schedule))), "assigned shifts"),
            ("Agents", format_number(summary.get("agent_pool_size", summary.get("agents_scheduled", 0))), "fixed roster"),
            ("Full Coverage Est.", format_number(summary.get("estimated_full_coverage_agents", 0)), "benchmark need"),
            ("Peak Need", format_number(summary.get("peak_required_agents", 0)), "agents required"),
            ("Peak Plan", format_number(summary.get("peak_scheduled_agents", 0)), "agents scheduled"),
            ("Coverage", f"{coverage_achieved:.1%}", "fulfilled demand"),
            ("Gap Intervals", format_number(summary.get("intervals_with_understaffing", understaffed_intervals)), "periods running short"),
        ]
    )
    st.caption(
        "Roster rules: one shift per agent per day, "
        f"max {summary.get('max_shifts_per_agent_per_week', 5)} shifts per week, "
        f"{summary.get('min_rest_hours', 11)}h minimum rest."
    )

    render_section_header(
        "Coverage Gap Over Time",
        "The chart compares required staffing, scheduled staffing, and understaffed intervals across the planning horizon. It shows where the simulated roster falls below required coverage.",
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=coverage["interval_start_datetime"],
            y=coverage["required_agents"],
            mode="lines",
            name="Required",
            line={"color": ACCENT_DARK, "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=coverage["interval_start_datetime"],
            y=coverage["scheduled_agents"],
            mode="lines",
            name="Scheduled",
            line={"color": ACCENT, "width": 2},
        )
    )
    fig.add_trace(
        go.Bar(
            x=coverage["interval_start_datetime"],
            y=coverage["understaffed_agents"],
            name="Understaffed",
            opacity=0.35,
            yaxis="y2",
            marker={"color": ACCENT_WARM},
        )
    )
    worst_gap = coverage.loc[coverage["understaffed_agents"].idxmax()]
    fig.add_annotation(
        x=worst_gap["interval_start_datetime"],
        y=worst_gap["required_agents"],
        text=f"Largest gap<br>{format_number(worst_gap['understaffed_agents'])}",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1,
        arrowcolor="#7c6f60",
        ax=46,
        ay=-35,
        bgcolor="rgba(248, 243, 234, 0.92)",
        bordercolor="#cbbfac",
        borderwidth=1,
        font={"color": INK, "size": 11},
    )
    fig.update_layout(title="Required vs scheduled coverage", xaxis_title=None, yaxis_title="Agents")
    fig.update_layout(yaxis2={"title": "Gap", "overlaying": "y", "side": "right"})
    add_chart_source(fig, "SIMULATED roster allocation")
    render_plotly_chart(fig)

    dates = sorted(schedule["shift_date"].dropna().unique())
    render_section_header(
        "Selected Day View",
        "The selected day view breaks the roster into individual shift windows and shows how scheduled supply aligns with required staffing across a single day.",
    )
    selected_date = st.selectbox("Schedule date", dates)
    day_schedule = schedule[schedule["shift_date"] == selected_date].sort_values(
        ["shift_start_datetime", "agent_name"]
    )
    day_schedule = day_schedule.assign(
        shift_window=day_schedule["shift_start_datetime"].dt.strftime("%H:%M")
        + "-"
        + day_schedule["shift_end_datetime"].dt.strftime("%H:%M")
    )
    day_coverage = coverage[coverage["interval_start_datetime"].dt.date == selected_date]
    shift_mix = (
        day_schedule.groupby("shift_window", as_index=False)
        .agg(agent_count=("agent_id", "count"))
        .sort_values("shift_window")
    )
    if not shift_mix.empty:
        render_chart_header(
            "Simulated Roster Allocation",
            "The bar chart shows the number of agents assigned to each shift window on the selected date.",
        )
        fig = px.bar(shift_mix, x="shift_window", y="agent_count", color_discrete_sequence=[ACCENT])
        fig.update_layout(title="Daily shift mix", xaxis_title=None, yaxis_title="Agents")
        add_chart_source(fig, "SIMULATED roster allocation")
        render_plotly_chart(fig)

    if not day_coverage.empty:
        render_chart_header(
            "Simulated Roster Allocation",
            "The intraday chart compares required staffing, scheduled staffing, and understaffed intervals for the selected date.",
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=day_coverage["interval_start_datetime"],
                y=day_coverage["required_agents"],
                mode="lines",
                name="Required",
                line={"color": ACCENT_DARK, "width": 2},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=day_coverage["interval_start_datetime"],
                y=day_coverage["scheduled_agents"],
                mode="lines",
                name="Scheduled",
                line={"color": ACCENT, "width": 2},
            )
        )
        fig.add_trace(
            go.Bar(
                x=day_coverage["interval_start_datetime"],
                y=day_coverage["understaffed_agents"],
                name="Understaffed",
                opacity=0.35,
                marker={"color": ACCENT_WARM},
            )
        )
        fig.update_layout(title="Selected-day coverage", xaxis_title=None, yaxis_title="Agents")
        add_chart_source(fig, "SIMULATED roster allocation")
        render_plotly_chart(fig)

    shift_options = ["All"] + shift_mix["shift_window"].tolist()
    selected_shift = st.selectbox("Shift window", shift_options)
    filtered_day_schedule = (
        day_schedule
        if selected_shift == "All"
        else day_schedule[day_schedule["shift_window"] == selected_shift]
    )
    roster_display = filtered_day_schedule[
        [
            "agent_id",
            "agent_name",
            "shift_window",
            "break_start_datetime",
            "break_end_datetime",
            "covered_intervals",
        ]
    ].copy()
    roster_display["break_start_datetime"] = roster_display["break_start_datetime"].dt.strftime("%H:%M")
    roster_display["break_end_datetime"] = roster_display["break_end_datetime"].dt.strftime("%H:%M")
    render_section_header(
        "Roster Detail",
        "Simulated agents are named after Agatha Christie characters. These names are fictional and used only to label the modeled roster.",
    )
    render_dataframe(roster_display, hide_index=True)

    with st.expander("Daily timeline"):
        timeline = px.timeline(
            filtered_day_schedule,
            x_start="shift_start_datetime",
            x_end="shift_end_datetime",
            y="agent_name",
            color="shift_window",
            color_discrete_sequence=EDITORIAL_COLORS,
        )
        timeline.update_yaxes(autorange="reversed")
        timeline.update_layout(
            title="Daily agent schedule",
            xaxis_title=None,
            yaxis_title=None,
            height=min(900, max(360, len(filtered_day_schedule) * 18)),
            showlegend=True,
        )
        add_chart_source(timeline, "SIMULATED roster allocation")
        render_plotly_chart(timeline)


def render_agent_performance(agents: pd.DataFrame, agent_dimension: pd.DataFrame) -> None:
    if agents.empty:
        st.info("Service quality metrics data is not available.")
        return
    render_chapter_header(
        "CHAPTER 06 · SERVICE QUALITY METRICS",
        "Synthetic Service Metrics",
        "This page shows the modeled service layer built on top of the simulated operation. No real employee performance data is used here.",
        "SYNTHETIC OPERATIONAL METADATA",
    )
    render_insight_callout(
        (
            "The charts and tables on this page summarize the synthetic workload assigned to the modeled "
            "agent pool. They show workload distribution and handle-time variation within the simulated environment."
        )
    )
    display = agents.copy()
    schedule_names = read_postgres_or_first_csv(
        "optimized_schedule",
        [
            DATA_DIR / "future_optimized_schedule.csv",
            DATA_DIR / "full_optimized_schedule.csv",
            DATA_DIR / "optimized_schedule_sample.csv",
        ],
    )
    name_lookup: dict[int, str] = {}
    if not schedule_names.empty and {"agent_id", "agent_name"}.issubset(schedule_names.columns):
        schedule_names["agent_id"] = pd.to_numeric(schedule_names["agent_id"])
        name_lookup = (
            schedule_names.dropna(subset=["agent_id", "agent_name"])
            .drop_duplicates("agent_id")
            .set_index("agent_id")["agent_name"]
            .to_dict()
        )
    if "agent_name" not in display.columns:
        display["agent_name"] = "Agent " + display["agent_id"].astype(str)
    display = apply_agent_name_lookup(display, name_lookup)
    agent_dimension = apply_agent_name_lookup(agent_dimension, name_lookup)
    total_agents = len(agent_dimension) if not agent_dimension.empty else display["agent_id"].nunique()
    agents_with_calls = display["agent_id"].nunique()
    grouped = (
        display.groupby(["agent_id", "agent_name"], as_index=False)
        .agg(
            handled_calls=("handled_calls", "sum"),
            avg_handle_time_sec=("avg_handle_time_sec", "mean"),
            avg_talk_time_sec=("avg_talk_time_sec", "mean"),
            avg_acw_time_sec=("avg_acw_time_sec", "mean"),
        )
        .sort_values("handled_calls", ascending=False)
    )
    render_metric_strip(
        [
            ("Total Agents", format_number(total_agents), "fictional roster"),
            ("Agents with Calls", format_number(agents_with_calls), "active in sample"),
            ("Handled Calls", format_number(grouped["handled_calls"].sum()), "synthetic workload"),
            ("Avg AHT", f"{grouped['avg_handle_time_sec'].mean():,.0f}s", "modeled handle time"),
        ]
    )

    if not agent_dimension.empty:
        render_chart_header(
            "Synthetic Agent Pool",
            "The chart shows how the modeled agent pool is distributed across service categories.",
        )
        skill_mix = (
            agent_dimension.groupby("skill_group", as_index=False)
            .agg(agent_count=("agent_id", "count"))
            .sort_values("agent_count", ascending=False)
        )
        fig = px.bar(skill_mix, x="skill_group", y="agent_count", color_discrete_sequence=[ACCENT])
        fig.update_layout(title="Agent pool by skill group", xaxis_title=None, yaxis_title="Agents")
        add_chart_source(fig, "SYNTHETIC agent entities")
        render_plotly_chart(fig)

    top_agents = grouped.head(20)
    render_chart_header(
        "Modeled Service Workload",
        "The bar chart ranks synthetic agents by handled call volume and colors them by average handle time. Agent names are fictional and used only for display.",
    )
    fig = px.bar(
        top_agents,
        x="agent_name",
        y="handled_calls",
        color="avg_handle_time_sec",
        color_continuous_scale=["#dfeaf5", ACCENT, ACCENT_DARK],
    )
    fig.update_layout(title="Top agents by handled calls", xaxis_title=None, yaxis_title="Calls")
    add_chart_source(fig, "SYNTHETIC agent performance metadata")
    render_plotly_chart(fig)

    render_section_header(
        "Synthetic Detail Table",
        "The table lists generated service metrics for the simulated agent pool, including handled calls, average handle time, average talk time, and average after-call work time.",
    )
    render_dataframe(top_agents, hide_index=True)


def render_methodology() -> None:
    sample = load_json(DOCS_DIR / "sample_generation_summary.json")
    full_dataset = load_json(DOCS_DIR / "full_dataset_summary.json")
    validation = {
        "Database": "CallCenterWFM",
        "Dim_Date": "1,096",
        "Dim_Time": "48",
        "Dim_Queue": "217",
        "Dim_Agent": "160",
        "Fact_Calls": "10,336,480",
        "Raw_NYC_311_Service_Requests": "10,336,480",
        "vw_Raw_NYC_311_Volume_30Min": "52,603",
        "vw_Volume_30Min": "2,230,984",
        "vw_Forecasting_Input": "252,790",
        "vw_Agent_Performance": "175,359",
    }

    render_chapter_header(
        "CHAPTER 07 · METHODS & ASSUMPTIONS",
        "Data Scope, Assumptions, and Modeling Boundaries",
        "This page documents which parts of the prototype are real, which are generated, and which are produced through forecasting or simulation.",
        "TRANSPARENCY APPENDIX",
    )
    render_insight_callout(
        (
            "The prototype combines real public demand with synthetic operational assumptions and simulated "
            "outcomes. This page defines those boundaries explicitly."
        )
    )

    render_section_header(
        "Pipeline Flow",
        "Each stage below shows how the prototype moves from raw demand into cleaned intervals, synthetic operational assumptions, forecast output, staffing calculations, and simulated roster coverage.",
    )
    st.markdown(
        """
        <div class="method-flow">
            <div class="method-card">
                <div class="method-card-title">NYC 311</div>
                <div class="method-card-note">Public service request timestamps and volumes.</div>
            </div>
            <div class="method-card">
                <div class="method-card-title">Cleaning</div>
                <div class="method-card-note">Dates, intervals, categories, and volume preparation.</div>
            </div>
            <div class="method-card synthetic">
                <div class="method-card-title">Synthetic Metadata</div>
                <div class="method-card-note">AHT, abandonment, SLA, and agent entities.</div>
            </div>
            <div class="method-card">
                <div class="method-card-title">Forecasting</div>
                <div class="method-card-note">Future 30-minute demand predictions.</div>
            </div>
            <div class="method-card simulated">
                <div class="method-card-title">Erlang C</div>
                <div class="method-card-note">Queue assumptions translated into required agents.</div>
            </div>
            <div class="method-card simulated">
                <div class="method-card-title">Roster Simulation</div>
                <div class="method-card-note">Shift allocation, gaps, and coverage outcomes.</div>
            </div>
            <div class="method-card">
                <div class="method-card-title">Dashboard</div>
                <div class="method-card-note">Analytical views and technical evidence.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section_header(
        "Real vs Synthetic",
        "The table below summarizes which data elements are observed, which are generated, and how each layer is used within the dashboard.",
    )
    transparency_rows = [
        {
            "Layer": "REAL",
            "Included data": "NYC 311 service request timestamps and demand volumes",
            "Use in dashboard": "Historical demand, interval volume, and service category trends",
        },
        {
            "Layer": "SYNTHETIC",
            "Included data": "AHT, hold time, abandonment, SLA flags, agent entities",
            "Use in dashboard": "Service-quality metrics and modeled operating KPIs",
        },
        {
            "Layer": "FORECASTED",
            "Included data": "Model predictions for future 30-minute demand intervals",
            "Use in dashboard": "Demand forecast, validation, and model comparison",
        },
        {
            "Layer": "SIMULATED",
            "Included data": "Staffing plans, roster assignments, and coverage outcomes",
            "Use in dashboard": "Capacity planning, roster simulation, and gap analysis",
        },
    ]
    render_dataframe(pd.DataFrame(transparency_rows), hide_index=True)

    assumptions_col, limitations_col = st.columns(2)
    with assumptions_col:
        render_section_header("Assumptions")
        st.markdown(
            """
            - AHT is synthetic and generated from service-category assumptions.
            - SLA outcomes are derived from modeled wait-time behavior.
            - Simulated agents use fictional Agatha Christie character names for display.
            - Erlang C assumes stationary interval demand, pooled agents, and simplified queue behavior.
            """
        )
    with limitations_col:
        render_section_header("Limitations")
        st.markdown(
            """
            - No real call center operations are observed.
            - No employee records are included.
            - Staffing rules are simplified for an academic prototype.
            - Results demonstrate a method, not live operations software.
            """
        )

    with st.expander("Validation evidence", expanded=False):
        left, right = st.columns(2)
        with left:
            st.subheader("Dataset Summary Payloads")
            st.json({"full_nyc_311_extract": full_dataset, "synthetic_sample": sample})
        with right:
            st.subheader("Database Object Summary")
            st.table(pd.DataFrame(validation.items(), columns=["Object", "Value"]))


def main() -> None:
    page_config()
    if not authenticate():
        return

    source, data = load_data()
    volume = data["volume_30min"]

    categories, date_range = render_sidebar(source, volume)
    filtered_volume = apply_filters(volume, categories, date_range)

    st.markdown(
        '<div class="app-shell-label">Call Center Workforce Management</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Overview",
            "Demand Analysis",
            "Demand Forecast",
            "Capacity Planning",
            "Roster Simulation",
            "Service Quality Metrics",
            "Methods & Assumptions",
        ]
    )

    with tabs[0]:
        render_executive_summary(filtered_volume)
    with tabs[1]:
        render_historical_trends(filtered_volume)
    with tabs[2]:
        render_forecasting(data["forecasting_input"])
    with tabs[3]:
        render_staffing()
    with tabs[4]:
        render_scheduling()
    with tabs[5]:
        render_agent_performance(data["agent_performance"], data["agent_dimension"])
    with tabs[6]:
        render_methodology()


if __name__ == "__main__":
    main()
