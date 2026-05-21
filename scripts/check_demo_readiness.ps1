param(
    [switch]$RequireSql
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
. (Join-Path $PSScriptRoot "_python_env.ps1")

function Write-ReadinessCheck {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [bool]$Passed,

        [string]$Detail = ""
    )

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    if ($Detail) {
        Write-Host "[$status] $Name - $Detail"
    }
    else {
        Write-Host "[$status] $Name"
    }
}

function Test-RequiredPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $exists = Test-Path $Path
    Write-ReadinessCheck -Name $Name -Passed $exists -Detail $Path
    return $exists
}

Push-Location $ProjectRoot
try {
    $failed = $false

    $Python = Get-ProjectPython -ProjectRoot $ProjectRoot
    Show-PythonSummary -Python $Python

    $requiredModules = @("streamlit", "pandas", "plotly", "sklearn", "ortools", "psycopg")
    foreach ($module in $requiredModules) {
        $installed = Test-PythonModule -Python $Python -Module $module
        Write-ReadinessCheck -Name "Python module '$module'" -Passed $installed
        if (-not $installed) {
            $failed = $true
        }
    }

    $artifactChecks = @(
        @{ Name = "Dashboard CSV call sample"; Path = "data\processed\synthetic_calls_sample.csv" },
        @{ Name = "Dashboard CSV forecasting sample"; Path = "data\processed\forecasting_input_sample.csv" },
        @{ Name = "Dashboard CSV baseline sample"; Path = "data\processed\baseline_forecast_sample.csv" },
        @{ Name = "Historical feature matrix"; Path = "data\processed\full_forecast_features.csv" },
        @{ Name = "Operational forecasting input"; Path = "data\processed\full_operational_forecasting_input.csv" },
        @{ Name = "Future forecast"; Path = "data\processed\future_sklearn_forecast.csv" },
        @{ Name = "Future staffing requirements"; Path = "data\processed\future_staffing_requirements.csv" },
        @{ Name = "Future optimized schedule"; Path = "data\processed\future_optimized_schedule.csv" },
        @{ Name = "Future schedule coverage"; Path = "data\processed\future_schedule_coverage.csv" },
        @{ Name = "Portfolio deployment schema"; Path = "deploy\postgres\001_schema.sql" },
        @{ Name = "Portfolio deployment seed"; Path = "deploy\seed\dashboard_volume_30min.csv" },
        @{ Name = "Forecast summary"; Path = "docs\future_forecast_summary.json" },
        @{ Name = "Staffing summary"; Path = "docs\future_staffing_requirements_summary.json" },
        @{ Name = "Scheduling summary"; Path = "docs\future_scheduling_summary.json" }
    )

    foreach ($check in $artifactChecks) {
        if (-not (Test-RequiredPath -Path $check.Path -Name $check.Name)) {
            $failed = $true
        }
    }

    if ($RequireSql) {
        if (-not (Test-PythonModule -Python $Python -Module "pyodbc")) {
            Write-ReadinessCheck -Name "SQL Server Python driver" -Passed $false -Detail "pyodbc is required for -RequireSql"
            $failed = $true
        }
        else {
            $sqlCheck = "import os, pyodbc; connection_string = os.getenv('CALLCENTER_SQL_CONNECTION') or 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=CallCenterWFM;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'; connection = pyodbc.connect(connection_string, timeout=5); cursor = connection.cursor(); cursor.execute('SELECT COUNT_BIG(*) FROM dbo.Fact_Calls'); print(cursor.fetchone()[0])"
            $rowCount = & $Python -c $sqlCheck
            $sqlPassed = $LASTEXITCODE -eq 0 -and [long]$rowCount -gt 0
            Write-ReadinessCheck -Name "SQL warehouse connection" -Passed $sqlPassed -Detail "Fact_Calls rows: $rowCount"
            if (-not $sqlPassed) {
                $failed = $true
            }
        }
    }
    else {
        Write-ReadinessCheck -Name "SQL warehouse connection" -Passed $true -Detail "Skipped. Add -RequireSql to verify SQL Server."
    }

    if ($failed) {
        throw "Demo readiness check failed. Resolve the failed checks above before the final rehearsal."
    }

    Write-Host "Demo readiness check passed."
}
finally {
    Pop-Location
}
