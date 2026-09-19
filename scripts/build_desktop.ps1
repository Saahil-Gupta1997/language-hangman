param([string]$Python = "python")
# Builds dist/LanguageHangman (PyInstaller) and dist/installer (Inno Setup 6) from this checkout.
# Pass -Python to use a specific interpreter, e.g. a clean Python 3.12 build environment.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Resolve-Path "$PSScriptRoot\..").Path
& $Python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Build dependencies failed." }
$version = (& $Python -c "import src; print(src.__version__)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $version) { throw "Could not read the application version." }
& $Python -m PyInstaller --clean --noconfirm packaging/hangman.spec
if ($LASTEXITCODE -ne 0) { throw "Application build failed." }
$candidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source,
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
if (-not $candidates) { throw "Install Inno Setup 6 to build the installer." }
& $candidates[0] "/DMyAppVersion=$version" packaging/hangman.iss
if ($LASTEXITCODE -ne 0) { throw "Installer build failed." }
# sha256sum-compatible lines: "<hash>  <file name>"
Get-ChildItem dist/installer/*.exe | ForEach-Object {
    "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLower(), $_.Name
} | Out-File -Encoding ascii dist/installer/SHA256.txt
Write-Host "Built Language Hangman $version"
