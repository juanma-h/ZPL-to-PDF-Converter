param(
  [string]$PythonExe = "python",
  [string]$DistDir = "dist/windows"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

$env:PIP_CACHE_DIR = Join-Path $RepoRoot "build/.pip-cache"
$env:PYINSTALLER_CONFIG_DIR = Join-Path $RepoRoot "build/.pyinstaller"

New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $env:PYINSTALLER_CONFIG_DIR | Out-Null

Write-Host "[1/4] Installing Python dependencies"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt pyinstaller

Write-Host "[2/4] Installing renderer dependencies"
Push-Location renderer
npm ci
Pop-Location

Write-Host "[3/4] Building executable with PyInstaller"
& $PythonExe -m PyInstaller --noconfirm --clean --distpath $DistDir --workpath build/tmp/win pyinstaller/main.spec

Write-Host "[4/4] Build ready at $DistDir"
