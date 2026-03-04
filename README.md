# ZPL to PDF/PNG Converter (Local, sin API)

Aplicacion de escritorio para convertir archivos ZPL (`.txt`) a:

- un PDF con todas las etiquetas
- multiples PNG (una imagen por etiqueta)

La conversion es **100% local**, sin depender de Labelary ni de internet.

## Stack

- UI desktop: `PySide6` (Python)
- Conversion a imagen: `zpl-renderer-js` (Node.js + WebAssembly, local)
- Union a PDF: `Pillow` (Python)

## Requisitos

- Python 3.11+ (recomendado)
- Node.js 20+ (recomendado)

## Instalacion

### 1) Dependencias Python

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Dependencias del renderer local

```bash
cd renderer
npm install
cd ..
```

## Ejecutar

```bash
python src/main.py
```

## Como funciona la conversion local

1. La app lee tu `.txt` con ZPL.
2. Ejecuta `renderer/render_zpl_local.mjs` con `node`.
3. El renderer genera PNG locales (sin red).
4. Si elegiste PDF, la app une los PNG en un unico PDF.

## Empaquetar para Windows (ejemplo)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ZPLConverter src/main.py
```

Si usas `--onefile`, recuerda incluir la carpeta `renderer` (script y dependencias) en tu instalador/distribucion final.

## macOS Apple Silicon (M1+)

- Usa una Mac Apple Silicon para generar binario nativo.
- Instala Python y Node en esa Mac.
- Repite los pasos de instalacion y empaquetado en macOS.

