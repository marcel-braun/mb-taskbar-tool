$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$spec = Join-Path $root "build\mbtaskbar.spec"
$dist = Join-Path $root "dist"
$work = Join-Path $root "build\tmp"

if (-not (Test-Path $python)) {
    throw "Virtuelle Umgebung nicht gefunden: $python`nErstelle sie zuerst mit: python -m venv .venv"
}

if (-not (Test-Path $spec)) {
    throw "PyInstaller-Spec nicht gefunden: $spec"
}

& $python -m PyInstaller $spec --distpath $dist --workpath $work
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Build erstellt: $(Join-Path $dist 'MbTaskbarTool.exe')"
