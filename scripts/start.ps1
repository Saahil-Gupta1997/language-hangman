param([switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath "$PSScriptRoot\..").Path
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Install Python 3.12 and run this launcher again." }
    & $pythonPath -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
}
$launchArguments = @("-m", "src.cli", "run-auth-gateway")
if (-not $NoBrowser) { $launchArguments += "--show-browser" }
& $pythonPath @launchArguments
if ($LASTEXITCODE -ne 0) { throw "Hangman could not start. See the error above." }
