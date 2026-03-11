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

1. La app lee el `.txt` con ZPL.
2. Ejecuta `renderer/render_zpl_local.mjs` con `node`.
3. El renderer genera PNG locales (sin red).
4. Si elegiste PDF, la app une los PNG en un unico PDF.

## Mejorar nitidez de letras y numeros

Si notas texto pixelado:

- Usa `Resolucion (dpmm)` entre `12` y `24` (300-600 DPI aprox).
- Usa `Calidad de render` en `Alta (2x recomendada)` o `Ultra (3x, mayor peso)`.
- Para etiquetas muy pequenas, prueba aumentar tambien el tamano de fuente en el ZPL si el diseno original usa fuentes muy compactas.

## Exportacion multicanal (etiquetas lado a lado)

Para rollos anchos donde las etiquetas van en paralelo:

- Ajusta `Canales por fila` a `2`, `3`, etc.
- La app agrupa las etiquetas en horizontal (lado a lado) en cada salida.
- En PDF, cada pagina representa una fila multicanal.
- En PNG, cada archivo generado representa una fila multicanal.

## Empaquetar para Windows (ejemplo)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ZPLConverter src/main.py
```

Si usas `--onefile`, recuerda incluir la carpeta `renderer` (script y dependencias) en tu instalador/distribucion final.
