param(
    [string]$StartDate = "2026-01-01",
    [string]$EndDate = "2026-01-31",
    [string]$Model = "hist_gradient_boosting",
    [string]$SqlServer = "localhost",
    [string]$Database = "CallCenterWFM",
    [int]$AgentCount = 160,
    [switch]$SkipSqlExport
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $ProjectRoot
try {
    if (-not $SkipSqlExport) {
        Write-Host "Exporting operational forecasting input from SQL Server..."
        Invoke-Sqlcmd `
            -ServerInstance $SqlServer `
            -Database $Database `
            -InputFile sql\exports\002_export_operational_forecasting_input_for_powershell.sql `
            -QueryTimeout 300 |
            Export-Csv -Path data\processed\full_operational_forecasting_input.csv -NoTypeInformation
    }

    Write-Host "Generating future call-volume forecast..."
    python src\forecasting\future_feature_forecast.py `
        --input data\processed\full_forecast_features.csv `
        --forecast-output data\processed\future_sklearn_forecast.csv `
        --feature-output data\processed\future_forecast_features.csv `
        --summary-output docs\future_forecast_summary.json `
        --all-models-output data\processed\future_model_scenario_forecasts.csv `
        --all-models-summary-output docs\future_model_scenario_summary.json `
        --start-date $StartDate `
        --end-date $EndDate `
        --model $Model

    Write-Host "Calculating Erlang C staffing requirements..."
    python src\workforce\erlang_c_staffing.py `
        --forecast data\processed\future_sklearn_forecast.csv `
        --forecasting-input data\processed\full_operational_forecasting_input.csv `
        --output data\processed\future_staffing_requirements.csv `
        --summary-output docs\future_staffing_requirements_summary.json

    Write-Host "Calculating model staffing scenarios..."
    python src\workforce\model_staffing_scenarios.py `
        --scenario-forecasts data\processed\future_model_scenario_forecasts.csv `
        --forecasting-input data\processed\full_operational_forecasting_input.csv `
        --output data\processed\future_model_staffing_scenarios.csv `
        --summary-output docs\future_model_staffing_scenario_summary.json `
        --agent-count $AgentCount

    Write-Host "Optimizing legal roster schedule..."
    python src\scheduling\agent_roster_optimizer.py `
        --requirements data\processed\future_staffing_requirements.csv `
        --schedule-output data\processed\future_optimized_schedule.csv `
        --coverage-output data\processed\future_schedule_coverage.csv `
        --summary-output docs\future_scheduling_summary.json `
        --agent-count $AgentCount `
        --max-shifts-per-agent-per-week 5 `
        --min-rest-hours 11 `
        --weekly-time-limit-sec 30

    Write-Host "Planning pipeline complete."
}
finally {
    Pop-Location
}
