$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath "$PSScriptRoot\..").Path
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Install Python 3.12 to run from source." }
}
& $pythonPath -m pip install -r requirements-desktop.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $pythonPath desktop_app.py
if ($LASTEXITCODE -ne 0) { throw "Hangman could not start." }
