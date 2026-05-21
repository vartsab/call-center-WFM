CREATE TABLE IF NOT EXISTS dashboard_volume_30min (
    calendar_date text,
    time_id text,
    interval_start_time text,
    half_hour_index text,
    queue_id text,
    queue_name text,
    service_category text,
    offered_calls text,
    answered_calls text,
    abandoned_calls text,
    avg_handle_time_sec text,
    avg_hold_time_sec text,
    service_level_rate text
);

CREATE TABLE IF NOT EXISTS dashboard_forecasting_input (
    interval_start_datetime text,
    half_hour_index text,
    day_of_week text,
    is_weekend text,
    is_holiday text,
    service_category text,
    call_volume text,
    avg_handle_time_sec text
);

CREATE TABLE IF NOT EXISTS dashboard_agent_performance (
    agent_id text,
    agent_name text,
    skill_group text,
    calendar_date text,
    handled_calls text,
    avg_handle_time_sec text,
    avg_talk_time_sec text,
    avg_acw_time_sec text
);

CREATE TABLE IF NOT EXISTS dashboard_agent_dimension (
    agent_id text,
    agent_name text,
    skill_group text,
    employment_type text,
    active_flag text
);

CREATE TABLE IF NOT EXISTS forecast_baseline (
    interval_start_datetime text,
    actual_call_volume text,
    predicted_call_volume text,
    absolute_error text,
    squared_error text,
    absolute_percentage_error text
);

CREATE TABLE IF NOT EXISTS forecast_best_holdout (
    interval_start_datetime text,
    actual_call_volume text,
    predicted_call_volume text,
    absolute_error text,
    squared_error text,
    absolute_percentage_error text
);

CREATE TABLE IF NOT EXISTS forecast_model_holdout_predictions (
    model text,
    interval_start_datetime text,
    actual_call_volume text,
    predicted_call_volume text,
    absolute_error text,
    squared_error text,
    absolute_percentage_error text
);

CREATE TABLE IF NOT EXISTS future_forecast (
    interval_start_datetime text,
    actual_call_volume text,
    predicted_call_volume text,
    absolute_error text,
    squared_error text,
    absolute_percentage_error text
);

CREATE TABLE IF NOT EXISTS future_model_scenario_forecasts (
    model text,
    interval_start_datetime text,
    predicted_call_volume text
);

CREATE TABLE IF NOT EXISTS staffing_requirements (
    interval_start_datetime text,
    actual_call_volume text,
    predicted_call_volume text,
    avg_handle_time_sec text,
    traffic_intensity_erlangs text,
    base_required_agents text,
    shrinkage_adjusted_agents text,
    expected_occupancy text,
    service_level_probability text,
    target_service_level text,
    sla_target_sec text,
    max_occupancy text,
    shrinkage_rate text
);

CREATE TABLE IF NOT EXISTS model_staffing_scenarios (
    model text,
    interval_start_datetime text,
    actual_call_volume text,
    predicted_call_volume text,
    avg_handle_time_sec text,
    traffic_intensity_erlangs text,
    base_required_agents text,
    shrinkage_adjusted_agents text,
    expected_occupancy text,
    service_level_probability text,
    target_service_level text,
    sla_target_sec text,
    max_occupancy text,
    shrinkage_rate text
);

CREATE TABLE IF NOT EXISTS optimized_schedule (
    agent_id text,
    agent_name text,
    shift_date text,
    shift_start_datetime text,
    shift_end_datetime text,
    break_start_datetime text,
    break_end_datetime text,
    covered_intervals text
);

CREATE TABLE IF NOT EXISTS schedule_coverage (
    interval_start_datetime text,
    required_agents text,
    scheduled_agents text,
    understaffed_agents text,
    overstaffed_agents text
);

CREATE INDEX IF NOT EXISTS idx_dashboard_volume_date_time ON dashboard_volume_30min (calendar_date, time_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_volume_category ON dashboard_volume_30min (service_category);
CREATE INDEX IF NOT EXISTS idx_forecast_baseline_interval ON forecast_baseline (interval_start_datetime);
CREATE INDEX IF NOT EXISTS idx_future_forecast_interval ON future_forecast (interval_start_datetime);
CREATE INDEX IF NOT EXISTS idx_staffing_interval ON staffing_requirements (interval_start_datetime);
CREATE INDEX IF NOT EXISTS idx_schedule_shift_date ON optimized_schedule (shift_date);
CREATE INDEX IF NOT EXISTS idx_coverage_interval ON schedule_coverage (interval_start_datetime);

TRUNCATE TABLE
    dashboard_volume_30min,
    dashboard_forecasting_input,
    dashboard_agent_performance,
    dashboard_agent_dimension,
    forecast_baseline,
    forecast_best_holdout,
    forecast_model_holdout_predictions,
    future_forecast,
    future_model_scenario_forecasts,
    staffing_requirements,
    model_staffing_scenarios,
    optimized_schedule,
    schedule_coverage;

\copy dashboard_volume_30min FROM '/seed/dashboard_volume_30min.csv' WITH (FORMAT csv, HEADER true);
\copy dashboard_forecasting_input FROM '/seed/dashboard_forecasting_input.csv' WITH (FORMAT csv, HEADER true);
\copy dashboard_agent_performance FROM '/seed/dashboard_agent_performance.csv' WITH (FORMAT csv, HEADER true);
\copy dashboard_agent_dimension FROM '/seed/dashboard_agent_dimension.csv' WITH (FORMAT csv, HEADER true);
\copy forecast_baseline FROM '/seed/forecast_baseline.csv' WITH (FORMAT csv, HEADER true);
\copy forecast_best_holdout FROM '/seed/forecast_best_holdout.csv' WITH (FORMAT csv, HEADER true);
\copy forecast_model_holdout_predictions FROM '/seed/forecast_model_holdout_predictions.csv' WITH (FORMAT csv, HEADER true);
\copy future_forecast FROM '/seed/future_forecast.csv' WITH (FORMAT csv, HEADER true);
\copy future_model_scenario_forecasts FROM '/seed/future_model_scenario_forecasts.csv' WITH (FORMAT csv, HEADER true);
\copy staffing_requirements FROM '/seed/staffing_requirements.csv' WITH (FORMAT csv, HEADER true);
\copy model_staffing_scenarios FROM '/seed/model_staffing_scenarios.csv' WITH (FORMAT csv, HEADER true);
\copy optimized_schedule FROM '/seed/optimized_schedule.csv' WITH (FORMAT csv, HEADER true);
\copy schedule_coverage FROM '/seed/schedule_coverage.csv' WITH (FORMAT csv, HEADER true);
