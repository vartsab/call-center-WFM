param(
    [int]$Port = 8501,

    [ValidateSet("Auto", "Sql", "Csv")]
    [string]$DataSource = "Csv"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
. (Join-Path $PSScriptRoot "_python_env.ps1")

Push-Location $ProjectRoot
try {
    $Python = Get-ProjectPython -ProjectRoot $ProjectRoot
    Show-PythonSummary -Python $Python
    Assert-PythonModules -Python $Python -Modules @("streamlit", "pandas", "plotly") -Purpose "dashboard demo"

    $env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
    $env:CALLCENTER_DASHBOARD_SOURCE = $DataSource.ToLowerInvariant()
    Write-Host "Starting Call Center WFM dashboard on http://localhost:$Port/"
    Write-Host "Dashboard data source mode: $DataSource"
    & $Python -m streamlit run app\streamlit\app.py --server.port $Port --server.headless true
}
finally {
    Pop-Location
}
