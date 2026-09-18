param([string]$OutputRoot = "release", [string]$PackageName = "")
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath "$PSScriptRoot\..").Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = "python" }
& $pythonPath (Join-Path $PSScriptRoot "build_release.py") --output $OutputRoot --name $PackageName
if ($LASTEXITCODE -ne 0) { throw "Release build failed." }
