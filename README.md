# ZPL to PDF/PNG Converter

Aplicacion de escritorio para convertir archivos ZPL (`.txt`) a:

- un PDF con todas las etiquetas
- multiples PNG
- composiciones multicanal por fila

La conversion es 100% local. No usa Labelary ni servicios externos.

## Mejoras de esta version

- UI renovada con tarjetas, resumen en vivo y una estetica inspirada en macOS Tahoe
- arquitectura modular en Python para separar UI, conversion, runtime y parsing
- persistencia de preferencias y ultimas rutas con `QSettings`
- soporte drag and drop para el archivo ZPL
- deteccion previa de etiquetas y cantidades (`^PQ`) antes de convertir
- build de Windows mejorado con `node.exe` embebido dentro del bundle
- CI alineado con los scripts reales de build
- pruebas unitarias para la logica desacoplada

## Stack

- UI desktop: `PySide6`
- renderer local: `zpl-renderer-js` sobre Node.js + WebAssembly
- PDF e imagenes: `Pillow`
- empaquetado: `PyInstaller`

## Estructura del repo

```text
.
|-- src/
|   |-- main.py
|   `-- zpl_converter/
|       |-- app.py
|       |-- conversion.py
|       |-- image_ops.py
|       |-- models.py
|       |-- renderer.py
|       |-- runtime.py
|       |-- zpl_parser.py
|       `-- ui/
|-- renderer/
|-- scripts/
|-- pyinstaller/
|-- tests/
`-- docs/
```

## Como funciona

1. La app analiza el `.txt` y estima cuantas etiquetas hay.
2. Python llama a `renderer/render_zpl_local.mjs`.
3. El runtime intenta usar primero `renderer/runtime/node(.exe)`.
4. Si no existe runtime embebido, usa `node` desde PATH.
5. El renderer produce PNG locales.
6. La app puede:
   - dejar los PNG tal cual
   - agruparlos por canales
   - unirlos en un PDF

## Desarrollo local

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

cd renderer
npm ci
cd ..

python src/main.py
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cd renderer
npm ci
cd ..

python src/main.py
```

## Pruebas

Con el entorno virtual del proyecto activo:

```powershell
$env:PYTHONPATH = "src"
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Build de Windows

### Build normal

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

Salida esperada:

- `dist/windows/ZPLConverter/`

### Build usando el `venv` actual

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 `
  -PythonExe .\venv\Scripts\python.exe `
  -DistDir dist/windows
```

### Build rapido si ya tienes todo instalado

```powershell
$env:SKIP_PYTHON_DEPS_INSTALL = "1"
$env:SKIP_NPM_INSTALL = "1"
$env:STRICT_EMBED_NODE_RUNTIME = "1"
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 `
  -PythonExe .\venv\Scripts\python.exe `
  -DistDir dist/windows
```

### Que hace el script de Windows

- instala dependencias de Python y renderer, salvo que uses `SKIP_*`
- detecta `node.exe` en PATH
- copia `node.exe` y las DLL vecinas a `renderer/runtime/`
- ejecuta `PyInstaller`
- genera una carpeta lista para distribuir

## Build de macOS

### Intel

```bash
./scripts/build_macos.sh x86_64 dist/macos-intel
```

### Apple Silicon

```bash
./scripts/build_macos.sh arm64 dist/macos-arm64
```

### Flags utiles

```bash
STRICT_EMBED_NODE_RUNTIME=1 ./scripts/build_macos.sh x86_64 dist/macos-intel
EMBED_NODE_RUNTIME=0 ./scripts/build_macos.sh x86_64 dist/macos-intel
CREATE_DMG=0 ./scripts/build_macos.sh x86_64 dist/macos-intel
SKIP_PYTHON_DEPS_INSTALL=1 SKIP_NPM_INSTALL=1 ./scripts/build_macos.sh x86_64 dist/macos-intel
```

## Variables utiles

- `STRICT_EMBED_NODE_RUNTIME=1`: falla si no se pudo embeber Node
- `EMBED_NODE_RUNTIME=0`: usa Node externo desde PATH
- `SKIP_PYTHON_DEPS_INSTALL=1`: no reinstala dependencias Python
- `SKIP_NPM_INSTALL=1`: no ejecuta `npm ci`
- `ZPL_CONVERTER_TEMP_DIR=/ruta`: fuerza un directorio de trabajo temporal

## CI

El workflow [build-multiplatform.yml](./.github/workflows/build-multiplatform.yml) ahora usa los scripts reales del repo:

- Windows x64
- macOS Intel
- macOS Apple Silicon

Eso evita que CI genere artefactos distintos a los builds locales.

## Documentacion adicional

- [Arquitectura](./docs/architecture.md)
- [Build de Windows](./docs/build-windows.md)
- [Packaging multiplataforma](./docs/packaging.md)

## Troubleshooting

### PowerShell bloquea el script

Ejecuta el build con:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

### No se encuentra Node.js

Instala Node.js 20+ y confirma:

```powershell
node -v
npm -v
```

### La app no encuentra el renderer local

Verifica que existan:

- `renderer/render_zpl_local.mjs`
- `renderer/node_modules/zpl-renderer-js`

### El bundle de Windows funciona en tu maquina pero no en otra

Genera el build con:

```powershell
$env:STRICT_EMBED_NODE_RUNTIME = "1"
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

Eso obliga a incluir `node.exe` dentro del bundle.
