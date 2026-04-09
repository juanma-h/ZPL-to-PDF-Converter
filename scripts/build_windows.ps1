param(
  [string]$PythonExe = "",
  [string]$DistDir = "dist/windows"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

$env:PIP_CACHE_DIR = Join-Path $RepoRoot "build/.pip-cache"
$env:PYINSTALLER_CONFIG_DIR = Join-Path $RepoRoot "build/.pyinstaller"
$EmbedNodeRuntime = if ($env:EMBED_NODE_RUNTIME) { $env:EMBED_NODE_RUNTIME } else { "1" }
$StrictEmbedNodeRuntime = if ($env:STRICT_EMBED_NODE_RUNTIME) { $env:STRICT_EMBED_NODE_RUNTIME } else { "0" }
$SkipPythonDepsInstall = if ($env:SKIP_PYTHON_DEPS_INSTALL) { $env:SKIP_PYTHON_DEPS_INSTALL } else { "0" }
$SkipNpmInstall = if ($env:SKIP_NPM_INSTALL) { $env:SKIP_NPM_INSTALL } else { "0" }
$RuntimeDir = Join-Path $RepoRoot "renderer/runtime"
$RuntimeNodeExe = Join-Path $RuntimeDir "node.exe"

New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $env:PYINSTALLER_CONFIG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if (-not $PythonExe) {
  $venvPython = Join-Path $RepoRoot "venv/Scripts/python.exe"
  if (Test-Path $venvPython) {
    $PythonExe = $venvPython
  } else {
    $PythonExe = "python"
  }
}

function Resolve-NodeBinary {
  $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
  if (-not $nodeCommand) {
    return $null
  }

  return (Resolve-Path $nodeCommand.Source).Path
}

function Embed-NodeRuntime {
  param(
    [Parameter(Mandatory = $true)]
    [string]$NodeBinary
  )

  $nodeDir = Split-Path -Parent $NodeBinary
  Remove-Item -LiteralPath $RuntimeNodeExe -Force -ErrorAction SilentlyContinue
  Get-ChildItem -Path $RuntimeDir -Filter *.dll -File -ErrorAction SilentlyContinue | Remove-Item -Force

  Copy-Item -LiteralPath $NodeBinary -Destination $RuntimeNodeExe -Force
  $copiedDlls = @()
  Get-ChildItem -Path $nodeDir -Filter *.dll -File -ErrorAction SilentlyContinue | ForEach-Object {
    $destination = Join-Path $RuntimeDir $_.Name
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    $copiedDlls += $_.Name
  }

  Write-Host "[preflight] Embedded Node runtime from $NodeBinary"
  if ($copiedDlls.Count -gt 0) {
    Write-Host "[preflight] Copied DLLs: $($copiedDlls -join ', ')"
  } else {
    Write-Host "[preflight] No adjacent Node DLLs were detected"
  }
}

$nodeBinary = Resolve-NodeBinary
if (-not $nodeBinary) {
  throw "Node.js no esta instalado o no esta en PATH."
}

Write-Host "[preflight] python: $PythonExe"
Write-Host "[preflight] node: $nodeBinary"
Write-Host "[preflight] embed runtime: $EmbedNodeRuntime"

if ($EmbedNodeRuntime -eq "1") {
  try {
    Embed-NodeRuntime -NodeBinary $nodeBinary
  } catch {
    if ($StrictEmbedNodeRuntime -eq "1") {
      throw "Fallo el embedding del runtime de Node y STRICT_EMBED_NODE_RUNTIME=1. $($_.Exception.Message)"
    }

    Write-Warning "No se pudo embeber el runtime de Node. El build continuara usando Node externo desde PATH."
    Remove-Item -LiteralPath $RuntimeNodeExe -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $RuntimeDir -Filter *.dll -File -ErrorAction SilentlyContinue | Remove-Item -Force
  }
} else {
  Write-Host "[preflight] Skipping embedded Node runtime (EMBED_NODE_RUNTIME=$EmbedNodeRuntime)"
}

if ($SkipPythonDepsInstall -eq "1") {
  Write-Host "[1/4] Skipping Python dependency installation"
} else {
  Write-Host "[1/4] Installing Python dependencies"
  & $PythonExe -m pip install --upgrade pip
  & $PythonExe -m pip install -r requirements.txt pyinstaller
}

if ($SkipNpmInstall -eq "1") {
  Write-Host "[2/4] Skipping renderer dependency installation"
} else {
  Write-Host "[2/4] Installing renderer dependencies"
  Push-Location renderer
  npm ci
  Pop-Location
}

Write-Host "[3/4] Building executable with PyInstaller"
& $PythonExe -m PyInstaller --noconfirm --clean --distpath $DistDir --workpath build/tmp/win pyinstaller/main.spec

Write-Host "[4/4] Build ready at $DistDir"
