"""Streamlit dashboard for the call center workforce management capstone."""

from __future__ import annotations

import json
import os
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


def page_config() -> None:
    st.set_page_config(
        page_title="Call Center WFM",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
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


def render_sidebar(source: str, volume: pd.DataFrame) -> tuple[list[str], tuple[Any, Any]]:
    st.sidebar.title("Call Center WFM")
    st.sidebar.caption(f"Data source: {source}")

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
    answered_calls = volume["answered_calls"].sum() if not volume.empty else 0
    abandoned_calls = volume["abandoned_calls"].sum() if not volume.empty else 0
    abandonment_rate = abandoned_calls / total_calls if total_calls else 0
    service_level = (
        (volume["service_level_rate"] * volume["offered_calls"]).sum() / total_calls
        if total_calls
        else 0
    )
    avg_aht = (
        (volume["avg_handle_time_sec"] * volume["answered_calls"]).sum() / answered_calls
        if answered_calls
        else 0
    )

    cols = st.columns(5)
    cols[0].metric("Offered calls", format_compact_number(total_calls))
    cols[1].metric("Answered calls", format_compact_number(answered_calls))
    cols[2].metric("Abandoned", format_compact_number(abandoned_calls))
    cols[3].metric("Abandonment", f"{abandonment_rate:.1%}")
    cols[4].metric("Avg AHT", f"{avg_aht:,.0f}s")

    daily = (
        volume.groupby("calendar_date", as_index=False)
        .agg(
            offered_calls=("offered_calls", "sum"),
            answered_calls=("answered_calls", "sum"),
            abandoned_calls=("abandoned_calls", "sum"),
        )
        .sort_values("calendar_date")
    )
    category = (
        volume.groupby("service_category", as_index=False)
        .agg(offered_calls=("offered_calls", "sum"))
        .sort_values("offered_calls", ascending=False)
    )

    left, right = st.columns([2, 1])
    with left:
        fig = px.line(daily, x="calendar_date", y="offered_calls", markers=True)
        fig.update_layout(title="Daily offered calls", yaxis_title="Calls", xaxis_title=None)
        render_plotly_chart(fig)
    with right:
        fig = px.bar(category, x="offered_calls", y="service_category", orientation="h")
        fig.update_layout(title="Service category mix", xaxis_title="Calls", yaxis_title=None)
        render_plotly_chart(fig)

    st.caption(f"Weighted service level: {service_level:.1%}")


def render_historical_trends(volume: pd.DataFrame) -> None:
    if volume.empty:
        st.info("Historical trend data is not available.")
        return

    interval = (
        volume.groupby("time_id", as_index=False)
        .agg(
            offered_calls=("offered_calls", "sum"),
            avg_handle_time_sec=("avg_handle_time_sec", "mean"),
            service_level_rate=("service_level_rate", "mean"),
        )
        .sort_values("time_id")
    )
    interval["time_label"] = interval["time_id"].astype(str).str.zfill(4)
    interval["time_label"] = interval["time_label"].str[:2] + ":" + interval["time_label"].str[2:]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=interval["time_label"], y=interval["offered_calls"], name="Calls"))
    fig.add_trace(
        go.Scatter(
            x=interval["time_label"],
            y=interval["service_level_rate"],
            name="SLA rate",
            yaxis="y2",
            mode="lines",
        )
    )
    fig.update_layout(
        title="Intraday demand and service level",
        xaxis_title=None,
        yaxis_title="Calls",
        yaxis2={"title": "SLA rate", "overlaying": "y", "side": "right", "tickformat": ".0%"},
        legend={"orientation": "h"},
    )
    render_plotly_chart(fig)

    heatmap = volume.groupby(["calendar_date", "time_id"], as_index=False).agg(
        offered_calls=("offered_calls", "sum")
    )
    heatmap["time_label"] = heatmap["time_id"].astype(str).str.zfill(4)
    heatmap["time_label"] = heatmap["time_label"].str[:2] + ":" + heatmap["time_label"].str[2:]
    pivot = heatmap.pivot(index="calendar_date", columns="time_label", values="offered_calls").fillna(0)
    fig = px.imshow(pivot, aspect="auto", labels={"color": "Calls"})
    fig.update_layout(title="30-minute call volume heatmap", xaxis_title=None, yaxis_title=None)
    render_plotly_chart(fig)


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

    metric_cols = st.columns(4)
    metric_cols[0].metric("Test intervals", summary.get("test_intervals", 0))
    metric_cols[1].metric("MAE", summary.get("mae", 0))
    metric_cols[2].metric("RMSE", summary.get("rmse", 0))
    metric_cols[3].metric("MAPE", f"{summary.get('mape', 0):.1%}")

    model_rows = pd.DataFrame(model_summary.get("models", [])) if model_summary else pd.DataFrame()
    model_names = model_rows["model"].tolist() if not model_rows.empty else []
    selected_model = model_summary.get("selected_model", "") if model_summary else ""

    if not model_rows.empty:
        st.subheader("Model comparison")
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

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=baseline["interval_start_datetime"],
            y=baseline["actual_call_volume"],
            mode="lines",
            name="Actual",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=baseline["interval_start_datetime"],
            y=baseline["predicted_call_volume"],
            mode="lines",
            name="Baseline",
        )
    )
    if selected_models and not model_predictions.empty:
        for model in selected_models:
            model_slice = model_predictions[model_predictions["model"] == model]
            fig.add_trace(
                go.Scatter(
                    x=model_slice["interval_start_datetime"],
                    y=model_slice["predicted_call_volume"],
                    mode="lines",
                    name=model_label(model),
                )
            )
    elif not feature_forecast.empty:
        fig.add_trace(
            go.Scatter(
                x=feature_forecast["interval_start_datetime"],
                y=feature_forecast["predicted_call_volume"],
                mode="lines",
                name=f"Best feature model ({model_label(selected_model or 'selected')})",
            )
        )
    fig.update_layout(title="Forecast holdout period", xaxis_title=None, yaxis_title="Calls")
    render_plotly_chart(fig)

    if not model_rows.empty:
        error_rows = model_rows.melt(
            id_vars="model",
            value_vars=[column for column in ["mae", "rmse", "mape"] if column in model_rows.columns],
            var_name="metric",
            value_name="value",
        )
        error_rows["model"] = error_rows["model"].map(model_label)
        fig = px.bar(error_rows, x="model", y="value", color="metric", barmode="group")
        fig.update_layout(title="Holdout error by model", xaxis_title=None, yaxis_title="Error")
        render_plotly_chart(fig)

    if not future_forecast.empty:
        future_forecast["interval_start_datetime"] = pd.to_datetime(
            future_forecast["interval_start_datetime"]
        )
        future_forecast["predicted_call_volume"] = pd.to_numeric(
            future_forecast["predicted_call_volume"]
        )
        st.subheader("Future planning forecast")
        future_cols = st.columns(4)
        future_cols[0].metric("Forecast intervals", future_summary.get("forecast_intervals", len(future_forecast)))
        future_cols[1].metric("Forecast start", future_summary.get("forecast_start", ""))
        future_cols[2].metric("Avg calls", f"{future_summary.get('avg_predicted_calls', 0):,.1f}")
        future_cols[3].metric("Peak calls", f"{future_summary.get('peak_predicted_calls', 0):,.1f}")
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
        fig.update_layout(title="Future 30-minute call forecast", xaxis_title=None, yaxis_title="Calls")
        render_plotly_chart(fig)

    if not forecasting.empty:
        top = (
            forecasting.groupby("service_category", as_index=False)
            .agg(call_volume=("call_volume", "sum"))
            .sort_values("call_volume", ascending=False)
        )
        fig = px.bar(top, x="service_category", y="call_volume")
        fig.update_layout(title="Forecasting input by category", xaxis_title=None, yaxis_title="Calls")
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

    metric_cols = st.columns(4)
    metric_cols[0].metric("Intervals", summary.get("interval_count", len(staffing)))
    metric_cols[1].metric("Peak base FTE", summary.get("peak_base_required_agents", 0))
    metric_cols[2].metric("Peak shrinkage FTE", summary.get("peak_shrinkage_adjusted_agents", 0))
    metric_cols[3].metric("Avg service level", f"{summary.get('avg_service_level_probability', 0):.1%}")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=staffing["interval_start_datetime"],
            y=staffing["base_required_agents"],
            mode="lines",
            name="Base required agents",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=staffing["interval_start_datetime"],
            y=staffing["shrinkage_adjusted_agents"],
            mode="lines",
            name="Shrinkage-adjusted agents",
        )
    )
    fig.add_trace(
        go.Bar(
            x=staffing["interval_start_datetime"],
            y=staffing["predicted_call_volume"],
            name="Predicted calls",
            yaxis="y2",
            opacity=0.35,
        )
    )
    fig.update_layout(
        title="Forecasted calls and required staffing",
        xaxis_title=None,
        yaxis_title="Agents",
        yaxis2={"title": "Calls", "overlaying": "y", "side": "right"},
        legend={"orientation": "h"},
    )
    render_plotly_chart(fig)

    scenario_rows = pd.DataFrame(scenario_summary.get("models", []))
    if not scenario_rows.empty:
        st.subheader("Model impact on staffing")
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
        scenario_plot = scenario_display.melt(
            id_vars="model",
            value_vars=["peak_shrinkage_adjusted_agents", "estimated_full_coverage_agents"],
            var_name="metric",
            value_name="agents",
        )
        fig = px.bar(scenario_plot, x="model", y="agents", color="metric", barmode="group")
        fig.update_layout(title="Staffing impact by forecast model", xaxis_title=None, yaxis_title="Agents")
        render_plotly_chart(fig)

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
        st.info("Optimized schedule output is not available.")
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

    metric_cols = st.columns(7)
    metric_cols[0].metric("Shifts", summary.get("scheduled_shifts", len(schedule)))
    metric_cols[1].metric("Agents", summary.get("agent_pool_size", summary.get("agents_scheduled", 0)))
    metric_cols[2].metric("Full roster", summary.get("estimated_full_coverage_agents", 0))
    metric_cols[3].metric("Peak need", summary.get("peak_required_agents", 0))
    metric_cols[4].metric("Peak plan", summary.get("peak_scheduled_agents", 0))
    metric_cols[5].metric("Coverage", f"{coverage_achieved:.1%}")
    metric_cols[6].metric("Gap intervals", summary.get("intervals_with_understaffing", 0))
    st.caption(
        "Roster rules: one shift per agent per day, "
        f"max {summary.get('max_shifts_per_agent_per_week', 5)} shifts per week, "
        f"{summary.get('min_rest_hours', 11)}h minimum rest."
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=coverage["interval_start_datetime"],
            y=coverage["required_agents"],
            mode="lines",
            name="Required",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=coverage["interval_start_datetime"],
            y=coverage["scheduled_agents"],
            mode="lines",
            name="Scheduled",
        )
    )
    fig.add_trace(
        go.Bar(
            x=coverage["interval_start_datetime"],
            y=coverage["understaffed_agents"],
            name="Understaffed",
            opacity=0.35,
            yaxis="y2",
        )
    )
    fig.update_layout(title="Required vs scheduled coverage", xaxis_title=None, yaxis_title="Agents")
    fig.update_layout(yaxis2={"title": "Gap", "overlaying": "y", "side": "right"})
    render_plotly_chart(fig)

    dates = sorted(schedule["shift_date"].dropna().unique())
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
        fig = px.bar(shift_mix, x="shift_window", y="agent_count")
        fig.update_layout(title="Daily shift mix", xaxis_title=None, yaxis_title="Agents")
        render_plotly_chart(fig)

    if not day_coverage.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=day_coverage["interval_start_datetime"],
                y=day_coverage["required_agents"],
                mode="lines",
                name="Required",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=day_coverage["interval_start_datetime"],
                y=day_coverage["scheduled_agents"],
                mode="lines",
                name="Scheduled",
            )
        )
        fig.add_trace(
            go.Bar(
                x=day_coverage["interval_start_datetime"],
                y=day_coverage["understaffed_agents"],
                name="Understaffed",
                opacity=0.35,
            )
        )
        fig.update_layout(title="Selected-day coverage", xaxis_title=None, yaxis_title="Agents")
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
    render_dataframe(roster_display, hide_index=True)

    with st.expander("Daily timeline"):
        timeline = px.timeline(
            filtered_day_schedule,
            x_start="shift_start_datetime",
            x_end="shift_end_datetime",
            y="agent_name",
            color="shift_window",
        )
        timeline.update_yaxes(autorange="reversed")
        timeline.update_layout(
            title="Daily agent schedule",
            xaxis_title=None,
            yaxis_title=None,
            height=min(900, max(360, len(filtered_day_schedule) * 18)),
            showlegend=True,
        )
        render_plotly_chart(timeline)


def render_agent_performance(agents: pd.DataFrame, agent_dimension: pd.DataFrame) -> None:
    if agents.empty:
        st.info("Agent performance data is not available.")
        return
    display = agents.copy()
    if "agent_name" not in display.columns:
        display["agent_name"] = "Agent " + display["agent_id"].astype(str)
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

    metric_cols = st.columns(4)
    metric_cols[0].metric("Total agents", total_agents)
    metric_cols[1].metric("Agents with calls", agents_with_calls)
    metric_cols[2].metric("Handled calls", format_number(grouped["handled_calls"].sum()))
    metric_cols[3].metric("Avg AHT", f"{grouped['avg_handle_time_sec'].mean():,.0f}s")

    if not agent_dimension.empty:
        skill_mix = (
            agent_dimension.groupby("skill_group", as_index=False)
            .agg(agent_count=("agent_id", "count"))
            .sort_values("agent_count", ascending=False)
        )
        fig = px.bar(skill_mix, x="skill_group", y="agent_count")
        fig.update_layout(title="Agent pool by skill group", xaxis_title=None, yaxis_title="Agents")
        render_plotly_chart(fig)

    top_agents = grouped.head(20)
    fig = px.bar(top_agents, x="agent_name", y="handled_calls", color="avg_handle_time_sec")
    fig.update_layout(title="Top agents by handled calls", xaxis_title=None, yaxis_title="Calls")
    render_plotly_chart(fig)
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

    left, right = st.columns(2)
    with left:
        st.subheader("Dataset summaries")
        st.json({"full_nyc_311_extract": full_dataset, "synthetic_sample": sample})
    with right:
        st.subheader("SQL validation")
        st.table(pd.DataFrame(validation.items(), columns=["Object", "Value"]))


def main() -> None:
    page_config()
    if not authenticate():
        return

    source, data = load_data()
    volume = data["volume_30min"]

    categories, date_range = render_sidebar(source, volume)
    filtered_volume = apply_filters(volume, categories, date_range)

    st.title("Call Center Workforce Management")

    tabs = st.tabs(
        [
            "Executive Summary",
            "Historical Trends",
            "Forecasting",
            "Staffing",
            "Scheduling",
            "Agent Performance",
            "Methodology",
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
