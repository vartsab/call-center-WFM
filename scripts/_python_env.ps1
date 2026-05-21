function Get-ProjectPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot
    )

    $candidatePaths = @(
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidatePaths) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand -and $pythonCommand.Source) {
        return $pythonCommand.Source
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyCommand -and $pyCommand.Source) {
        return $pyCommand.Source
    }

    throw "Python was not found. Create a virtual environment with 'python -m venv .venv', then install requirements."
}

function Show-PythonSummary {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Python
    )

    $summary = & $Python -c "import sys; print(f'{sys.executable} ({sys.version.split()[0]})')"
    Write-Host "Using Python: $summary"
}

function Test-PythonModule {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Python,

        [Parameter(Mandatory = $true)]
        [string]$Module
    )

    & $Python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$Module') else 1)" *> $null
    return $LASTEXITCODE -eq 0
}

function Assert-PythonModules {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Python,

        [Parameter(Mandatory = $true)]
        [string[]]$Modules,

        [string]$Purpose = "this workflow"
    )

    $missing = @(
        foreach ($module in $Modules) {
            if (-not (Test-PythonModule -Python $Python -Module $module)) {
                $module
            }
        }
    )

    if ($missing.Count -gt 0) {
        $moduleList = $missing -join ", "
        $installCommand = "& `"$Python`" -m pip install -r requirements.txt"
        throw "Missing Python modules for ${Purpose}: $moduleList. Install dependencies with: $installCommand"
    }
}
