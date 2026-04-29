<#
.SYNOPSIS
  Local Windows build of Lexora AI (onedir EXE + MSI), mirrors the CI workflow.

.DESCRIPTION
  Produces:
    dist\LexoraAI\LexoraAI.exe           (run directly, no install needed)
    LexoraAI-windows-amd64.zip           (portable zip)
    LexoraAI-windows-amd64.msi           (installer with Start Menu / Desktop shortcut options)

.PARAMETER Version
  MSI ProductVersion as n.n.n.n (default: 0.0.0.0 for local builds).

.PARAMETER SkipMsi
  Build the EXE + ZIP only, skip the WiX MSI step.

.PARAMETER SkipInstall
  Skip the `pip install` steps (useful if you've already set up .venv and just
  want to re-run pyinstaller / WiX).

.EXAMPLE
  # Full build (first time)
  .\packaging\windows\build-local.ps1

.EXAMPLE
  # Rebuild quickly, skip dependency installation
  .\packaging\windows\build-local.ps1 -SkipInstall

.EXAMPLE
  # Just the EXE + ZIP, don't touch WiX
  .\packaging\windows\build-local.ps1 -SkipMsi
#>

[CmdletBinding()]
param(
  [string]$Version = "0.0.0.0",
  [switch]$SkipMsi,
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

# Run from repo root regardless of where the script is invoked.
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot
Write-Host "Repo root: $repoRoot" -ForegroundColor Cyan

$appName = "LexoraAI"

# --- 1) venv + deps ---------------------------------------------------------
if (-not $SkipInstall) {
  if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Creating .venv..." -ForegroundColor Cyan
    python -m venv .venv
  }
  . .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  pip install .
  pip install "pyinstaller>=6.3,<7" "pillow>=10,<12"
} else {
  . .\.venv\Scripts\Activate.ps1
}

# Sanity-check that all critical runtime deps are importable in the active
# environment. PyInstaller can only bundle what it can see, so if any of
# these are missing (e.g. you ran -SkipInstall after wiping the venv)
# the build would otherwise produce an installer that crashes at first run.
Write-Host "`n=== Verifying critical runtime imports ===" -ForegroundColor Cyan
$probe = @"
import importlib, sys
mods = [
  ('cryptography', 'cryptography'),
  ('cryptography.fernet', 'cryptography.fernet'),
  ('flet', 'flet'),
  ('lexora', 'lexora'),
  ('lexora.secrets', 'lexora.secrets'),
]
missing = []
for label, name in mods:
  try:
    importlib.import_module(name)
    print(f'  OK  {label}')
  except Exception as e:
    print(f'  FAIL {label}: {e}')
    missing.append(label)
if missing:
  sys.exit('Missing modules: ' + ', '.join(missing))
"@
$probe | python -
if ($LASTEXITCODE -ne 0) {
  throw "Pre-build import check failed. Run without -SkipInstall to reinstall dependencies."
}

# --- 2) onedir PyInstaller build -------------------------------------------
Write-Host "`n=== Building onedir EXE ===" -ForegroundColor Cyan
if (Test-Path .\dist)  { Remove-Item .\dist  -Recurse -Force }
if (Test-Path .\build) { Remove-Item .\build -Recurse -Force }

pyinstaller --noconfirm --clean --distpath dist --workpath build `
  packaging\windows\lexora_ai.spec

$exePath = ".\dist\$appName\$appName.exe"
if (-not (Test-Path $exePath)) {
  throw "Build failed: $exePath not found."
}
Write-Host "Built: $exePath" -ForegroundColor Green
Write-Host "  Size: $([math]::Round((Get-Item $exePath).Length / 1MB, 1)) MB (launcher)"
$folderSize = (Get-ChildItem ".\dist\$appName" -Recurse | Measure-Object Length -Sum).Sum
Write-Host "  Folder total: $([math]::Round($folderSize / 1MB, 1)) MB"

# --- 3) ZIP artifact --------------------------------------------------------
$zipName = "$appName-windows-amd64.zip"
if (Test-Path $zipName) { Remove-Item $zipName -Force }
Compress-Archive -Path "dist\$appName" -DestinationPath $zipName
Write-Host "Created ZIP: $zipName" -ForegroundColor Green

# --- 4) MSI -----------------------------------------------------------------
if ($SkipMsi) {
  Write-Host "`nSkipping MSI build (-SkipMsi)." -ForegroundColor Yellow
  Write-Host "`nTest the portable build:" -ForegroundColor Cyan
  Write-Host "  .\dist\$appName\$appName.exe"
  exit 0
}

Write-Host "`n=== Locating WiX Toolset ===" -ForegroundColor Cyan
$wixBin = $null
$candidates = Get-ChildItem "${env:ProgramFiles(x86)}" -Directory -Filter "WiX Toolset*" -ErrorAction SilentlyContinue
foreach ($c in $candidates) {
  $candle = Join-Path $c.FullName "bin\candle.exe"
  if (Test-Path $candle) { $wixBin = Split-Path $candle -Parent; break }
}
if (-not $wixBin) {
  throw "WiX 3.x not found. Install it: choco install wixtoolset --version=3.14.1 -y"
}
Write-Host "WiX bin: $wixBin" -ForegroundColor Green

# Validate version string
if ($Version -notmatch '^\d+\.\d+\.\d+\.\d+$') {
  throw "Version must be n.n.n.n, got: $Version"
}

# Intermediates in a temp folder so we don't pollute the workspace
$wixOut = Join-Path $env:TEMP "lexora-wixout"
Remove-Item $wixOut -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $wixOut | Out-Null

$harvestDir    = (Resolve-Path "dist\$appName").Path
$harvestedWxs  = Join-Path $wixOut "LexoraComponents.wxs"
$productObj    = Join-Path $wixOut "Product.wixobj"
$harvestedObj  = Join-Path $wixOut "LexoraComponents.wixobj"
$msiName       = "$appName-windows-amd64.msi"

# 4a) heat.exe: harvest the onedir folder
Write-Host "`n=== heat: harvesting $harvestDir ===" -ForegroundColor Cyan
& (Join-Path $wixBin "heat.exe") dir $harvestDir `
  -cg LexoraComponents `
  -dr APPLICATIONFOLDER `
  -srd -sreg -scom -sfrag -gg -ke `
  -var "var.HarvestSource" `
  -out $harvestedWxs
if (-not (Test-Path $harvestedWxs)) { throw "heat.exe failed." }

# 4b) candle.exe: compile both WXS files
Write-Host "`n=== candle: compiling WXS ===" -ForegroundColor Cyan
& (Join-Path $wixBin "candle.exe") -arch x64 `
  "-dHarvestSource=$harvestDir" `
  "-dSourceDir=$harvestDir" `
  "-dProductVersion=$Version" `
  -out "$productObj" `
  "packaging\windows\Product.wxs"

& (Join-Path $wixBin "candle.exe") -arch x64 `
  "-dHarvestSource=$harvestDir" `
  -out "$harvestedObj" `
  "$harvestedWxs"

# 4c) light.exe: link into MSI
Write-Host "`n=== light: linking MSI ===" -ForegroundColor Cyan
& (Join-Path $wixBin "light.exe") -ext WixUIExtension `
  -out $msiName `
  "$productObj" "$harvestedObj"

if (-not (Test-Path $msiName)) { throw "MSI link failed." }

Write-Host "`nDone." -ForegroundColor Green
Write-Host "Artifacts:" -ForegroundColor Cyan
Write-Host "  Portable EXE : .\dist\$appName\$appName.exe"
Write-Host "  Portable ZIP : .\$zipName"
Write-Host "  Installer    : .\$msiName (ProductVersion $Version)"

Write-Host "`nNext steps to verify:" -ForegroundColor Cyan
Write-Host "  1) Portable  : .\dist\$appName\$appName.exe"
Write-Host "  2) Install   : msiexec /i $msiName /l*v install.log"
Write-Host "     - On 'Custom Setup', confirm 'Start menu shortcut' and 'Desktop shortcut' are both present and checked."
Write-Host "     - After install, check All Users desktop and Start Menu for 'Lexora AI'."
Write-Host "  3) Uninstall : msiexec /x $msiName /l*v uninstall.log"
