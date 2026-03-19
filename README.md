# ZPL to PDF/PNG Converter (Local, sin API)

Aplicacion de escritorio para convertir archivos ZPL (`.txt`) a:

- un PDF con todas las etiquetas
- multiples PNG (una imagen por etiqueta)

La conversion es 100% local, sin depender de Labelary ni de internet.

## Que hace

- Convierte ZPL a PNG usando `zpl-renderer-js` de forma local
- Une multiples etiquetas en un solo PDF con `Pillow`
- Permite exportacion multicanal (`Canales por fila`) para etiquetas lado a lado
- Mantiene el renderer dentro del proyecto para no depender de servicios externos

## Stack

- UI desktop: `PySide6` (Python)
- Render local: `zpl-renderer-js` (Node.js + WebAssembly)
- Union a PDF: `Pillow` (Python)

## Requisitos

- Python 3.11 a 3.14
- Recomendado: Python 3.11 o 3.12
- Node.js 20+

## Desarrollo local

Estas instrucciones son para ejecutar la app en modo desarrollo. Los scripts de build ya instalan dependencias por su cuenta.

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

### Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

cd renderer
npm ci
cd ..

python src/main.py
```

## Como funciona la conversion

1. La app lee el archivo `.txt` con ZPL.
2. Ejecuta `renderer/render_zpl_local.mjs`.
3. En macOS empaquetado, intenta usar un runtime de Node embebido en `renderer/runtime/node`.
4. Si no existe runtime embebido, usa `node` desde PATH.
5. El renderer genera PNG locales.
6. Si eliges PDF, la app une los PNG en un unico archivo.

## Calidad de salida

Si notas texto pixelado:

- Usa `Resolucion (dpmm)` entre `12` y `24` (300-600 DPI aprox.)
- Usa `Calidad de render` en `Alta (2x recomendada)` o `Ultra (3x, mayor peso)`
- Para etiquetas muy pequenas, revisa tambien el tamano de fuente en el ZPL original

## Exportacion multicanal

Para rollos anchos donde las etiquetas van en paralelo:

- Ajusta `Canales por fila` a `2`, `3`, etc.
- La app agrupa las etiquetas en horizontal dentro de cada salida
- En PDF, cada pagina representa una fila multicanal
- En PNG, cada archivo generado representa una fila multicanal

## Builds

### Windows x64

```powershell
./scripts/build_windows.ps1
```

Salida esperada:

- `dist/windows/ZPLConverter/`

### macOS Intel

```bash
./scripts/build_macos.sh x86_64 dist/macos-intel
```

Salida esperada:

- `dist/macos-intel/ZPLConverter.app`
- `dist/macos-intel/ZPLConverter-x86_64.dmg`

### macOS Apple Silicon

```bash
./scripts/build_macos.sh arm64 dist/macos-arm64
```

Salida esperada:

- `dist/macos-arm64/ZPLConverter.app`
- `dist/macos-arm64/ZPLConverter-arm64.dmg`

### Nota importante para distribucion en macOS

El script `scripts/build_macos.sh` intenta embeber `renderer/runtime/node` y las librerias dinamicas que ese binario necesita. Eso es lo recomendado si vas a pasar el `.dmg` a otra Mac sin instalar Node manualmente.

Comandos utiles:

```bash
STRICT_EMBED_NODE_RUNTIME=1 ./scripts/build_macos.sh x86_64 dist/macos-intel
EMBED_NODE_RUNTIME=0 ./scripts/build_macos.sh x86_64 dist/macos-intel
CREATE_DMG=0 ./scripts/build_macos.sh x86_64 dist/macos-intel
```

Que hace cada uno:

- `STRICT_EMBED_NODE_RUNTIME=1`: falla el build si no se pudo embeber Node
- `EMBED_NODE_RUNTIME=0`: omite el runtime embebido y usa `node` externo desde PATH
- `CREATE_DMG=0`: genera la app pero no crea el `.dmg`

> Para distribucion a usuarios finales en macOS, usa siempre `STRICT_EMBED_NODE_RUNTIME=1`.
> La app aun no esta firmada ni notarizada; para eso revisa `docs/packaging.md`.

## Troubleshooting

### Error: `npm: command not found` en macOS

Ese error indica que Node.js/npm no esta instalado o no esta en PATH.

Instalacion recomendada con Homebrew:

**Intel Mac**

```bash
brew install node@20
echo 'export PATH="/usr/local/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
node -v
npm -v
```

**Apple Silicon (M1+)**

```bash
brew install node@20
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
node -v
npm -v
```

### Error: `No matching distribution found for PySide6...`

Si aparece un error de ruedas incompatibles con PySide6 o Python 3.14:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Luego reintenta el build:

```bash
./scripts/build_macos.sh x86_64 dist/macos-intel
```

### Error: build de macOS con archivos viejos o caches inconsistentes

Si actualizaste la rama y sigues viendo errores viejos, limpia y vuelve a probar:

```bash
rm -rf build dist renderer/runtime build/node-runtime-libs.txt
./scripts/build_macos.sh x86_64 dist/macos-intel
```

## Estructura del repositorio

```text
.
├── src/                      # App principal (Python + PySide6)
├── renderer/                 # Render local de ZPL con Node + WASM
├── pyinstaller/              # Spec y configuracion de empaquetado
├── scripts/                  # Scripts de build por plataforma
├── .github/workflows/        # CI para builds multiplataforma
└── docs/                     # Documentacion adicional
```

## Documentacion adicional

- `docs/packaging.md`: detalle de packaging, CI/CD y firma/notarizacion en macOS
