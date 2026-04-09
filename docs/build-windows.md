# Build de Windows

## Requisitos

- Windows x64
- Python 3.11 a 3.14
- Node.js 20+
- PowerShell

## Preparacion recomendada

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller

cd renderer
npm ci
cd ..
```

## Comando recomendado

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 `
  -PythonExe .\venv\Scripts\python.exe `
  -DistDir dist/windows
```

## Salida esperada

- `dist/windows/ZPLConverter/ZPLConverter.exe`
- `dist/windows/ZPLConverter/_internal/renderer/runtime/node.exe`

## Build rapido sin reinstalar dependencias

```powershell
$env:SKIP_PYTHON_DEPS_INSTALL = "1"
$env:SKIP_NPM_INSTALL = "1"
$env:STRICT_EMBED_NODE_RUNTIME = "1"

powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 `
  -PythonExe .\venv\Scripts\python.exe `
  -DistDir dist/windows
```

## Variables soportadas

- `EMBED_NODE_RUNTIME=1`
  Comportamiento por defecto. Copia `node.exe` al bundle.
- `STRICT_EMBED_NODE_RUNTIME=1`
  Falla si no se pudo embeber Node.
- `SKIP_PYTHON_DEPS_INSTALL=1`
  No ejecuta `pip install`.
- `SKIP_NPM_INSTALL=1`
  No ejecuta `npm ci`.

## Verificacion minima

Despues del build, revisa:

```powershell
Test-Path .\dist\windows\ZPLConverter\ZPLConverter.exe
Test-Path .\dist\windows\ZPLConverter\_internal\renderer\runtime\node.exe
```

## Problemas comunes

### PowerShell bloquea el script

Usa siempre:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

### No se embebe Node

Comprueba:

```powershell
node -v
Get-Command node
```

Y reintenta con:

```powershell
$env:STRICT_EMBED_NODE_RUNTIME = "1"
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

### Quieres probar un build rapido en esta misma maquina

Usa `SKIP_PYTHON_DEPS_INSTALL=1` y `SKIP_NPM_INSTALL=1` si ya preparaste el entorno.
