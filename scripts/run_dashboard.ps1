param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $ProjectRoot
try {
    Write-Host "Starting Call Center WFM dashboard on http://localhost:$Port/"
    python -m streamlit run app\streamlit\app.py --server.port $Port
}
finally {
    Pop-Location
}
