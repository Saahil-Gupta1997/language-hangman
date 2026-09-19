$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Resolve-Path "$PSScriptRoot\..").Path
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Build dependencies failed." }
python -m PyInstaller --clean --noconfirm packaging/hangman.spec
if ($LASTEXITCODE -ne 0) { throw "Application build failed." }
$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $inno = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $inno)) { throw "Install Inno Setup 6 to build the installer." }
} else { $inno = $iscc.Source }
& $inno packaging/hangman.iss
if ($LASTEXITCODE -ne 0) { throw "Installer build failed." }
Get-ChildItem dist/installer/*.exe | Get-FileHash -Algorithm SHA256 |
    Format-List | Out-File dist/installer/SHA256.txt
