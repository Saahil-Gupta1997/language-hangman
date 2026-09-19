param([string]$Python = "python")
# Builds dist/LanguageHangman (PyInstaller) and dist/installer (Inno Setup 6) from this checkout.
# Pass -Python to use a specific interpreter, e.g. a clean Python 3.12 build environment.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Resolve-Path "$PSScriptRoot\..").Path

function Invoke-Native([scriptblock]$Command, [string]$Failure) {
    # Tools such as pip and PyInstaller log to stderr. Windows PowerShell 5.1 turns that into
    # terminating errors when output is captured, so rely on the exit code instead.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $Command } finally { $ErrorActionPreference = $previous }
    if ($LASTEXITCODE -ne 0) { throw $Failure }
}

Invoke-Native { & $Python -m pip install --disable-pip-version-check -r requirements-build.txt } "Build dependencies failed."
$version = (& $Python -c "import src; print(src.__version__)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $version) { throw "Could not read the application version." }
Invoke-Native { & $Python -m PyInstaller --clean --noconfirm packaging/hangman.spec } "Application build failed."
# Select-Object keeps a single path intact (indexing a lone string would return a character).
$iscc = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source,
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $iscc) { throw "Install Inno Setup 6 to build the installer." }
Invoke-Native { & $iscc "/DMyAppVersion=$version" packaging/hangman.iss } "Installer build failed."
# sha256sum-compatible lines: "<hash>  <file name>"
Get-ChildItem dist/installer/*.exe | ForEach-Object {
    "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLower(), $_.Name
} | Out-File -Encoding ascii dist/installer/SHA256.txt
Write-Host "Built Language Hangman $version"
