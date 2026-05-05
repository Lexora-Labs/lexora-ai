<#
.SYNOPSIS
  After heat.exe, assign a stable WiX File Id to LexoraAI.exe for advertised shortcuts.

.NOTES
  Product.wxs shortcuts use Target="[#LexoraAILauncherExe]". Heat emits random fil* ids,
  so we normalize the launcher row once per build.
#>
param(
  [Parameter(Mandatory)]
  [string]$HarvestedWxsPath
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $HarvestedWxsPath)) {
  throw "Harvested WiX not found: $HarvestedWxsPath"
}

$lines = Get-Content -LiteralPath $HarvestedWxsPath
$stableId = "LexoraAILauncherExe"
$patched = $false
$out = foreach ($line in $lines) {
  if (-not $patched -and
      $line -match '<File\s+Id="fil[0-9A-Fa-f]+"' -and
      $line -match '[\\/]LexoraAI\.exe"' ) {
    $patched = $true
    $line -replace 'Id="fil[0-9A-Fa-f]+"', "Id=`"$stableId`""
  }
  else {
    $line
  }
}

if (-not $patched) {
  throw "Could not find File row for LexoraAI.exe under HarvestSource in: $HarvestedWxsPath"
}

$out | Set-Content -LiteralPath $HarvestedWxsPath -Encoding utf8
Write-Host "WiX harvest patch: launcher File Id -> $stableId" -ForegroundColor Green
