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

- Python 3.11 a 3.14 (recomendado: 3.11 o 3.12)
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


## Troubleshooting de empaquetado (macOS)

Si ves errores como:

- `No matching distribution found for PySide6==6.8.1`
- conflictos de versiones con Python 3.14

haz lo siguiente:

1. Asegura un entorno virtual limpio.
2. Actualiza `pip` dentro del venv.
3. Reinstala dependencias desde `requirements.txt` (ahora con rangos compatibles).

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Luego vuelve a ejecutar el build de macOS Intel:

```bash
./scripts/build_macos.sh x86_64 dist/macos-intel
```


### Error: `npm: command not found` en macOS

Ese error indica que no tienes Node.js/npm instalado en tu Mac (o no esta en PATH).

Instalacion recomendada (Homebrew):

```bash
brew install node@20
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
node -v
npm -v
```

Luego reintenta:

```bash
./scripts/build_macos.sh x86_64 dist/macos-intel
```

### Error: `script ... pyinstaller/src/main.py not found`

Ese error ocurria por una resolucion relativa del `.spec`.
La configuracion actual ya usa rutas absolutas basadas en la ubicacion real del archivo `pyinstaller/main.spec`.

Si te aparece despues de actualizar, limpia caches y reintenta:

```bash
rm -rf build dist
./scripts/build_macos.sh x86_64 dist/macos-intel
```

Los scripts actuales ya redirigen los caches de `pip` y PyInstaller a `build/`, para evitar problemas de permisos sobre `~/Library/...`.

## Estructura recomendada del repositorio

```text
.
├── src/                      # App principal (Python + PySide6)
├── renderer/                 # Renderizador local de ZPL con Node
├── pyinstaller/              # Spec y configuracion de empaquetado
├── scripts/                  # Scripts de build por plataforma
├── .github/workflows/        # CI para builds multiplataforma
└── docs/                     # Documentacion adicional
```

## Build multiplataforma (una sola base de codigo)

### Windows x64

```powershell
./scripts/build_windows.ps1
```

### macOS Intel

```bash
./scripts/build_macos.sh x86_64 dist/macos-intel
```

### macOS Apple Silicon (M1+)

```bash
./scripts/build_macos.sh arm64 dist/macos-arm64
```

Nota tecnica: con PyInstaller + archivo `.spec`, la arquitectura se configura en el `.spec` (variable `PYINSTALLER_TARGET_ARCH`) y no por `--target-arch` en la linea de comandos.

> Nota: Para detalle de CI/CD y pasos de distribucion en macOS (firma/notarizacion), revisa `docs/packaging.md`.

## Empaquetar para Windows (ejemplo rapido)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ZPLConverter src/main.py
```

Si usas `--onefile`, recuerda incluir la carpeta `renderer` (script y dependencias) en tu instalador/distribucion final.
