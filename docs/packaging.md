# Estrategia de empaquetado multiplataforma

Este repositorio soporta una sola base de codigo para tres distribuciones:

- Windows x64
- macOS Intel (x86_64)
- macOS Apple Silicon (arm64, M1+)

## Estructura recomendada

```text
.
├── src/                      # Codigo Python de la app
├── renderer/                 # Render local ZPL (Node + WASM)
├── pyinstaller/
│   └── main.spec             # Definicion de PyInstaller
├── scripts/
│   ├── build_windows.ps1     # Build local para Windows
│   └── build_macos.sh        # Build local para macOS (Intel/ARM)
├── .github/workflows/
│   └── build-multiplatform.yml
└── docs/
    └── packaging.md
```

## Requisito clave de runtime

La app intenta usar primero un runtime de Node.js embebido dentro de `renderer/runtime/node` (incluido en el bundle de PyInstaller durante el build de macOS). Si no existe, usa `node` desde PATH.

Tambien requiere un entorno Python con dependencias compatibles (PySide6 y Pillow se definen por rango en `requirements.txt`).

> Recomendacion: para distribucion a usuarios finales en macOS, usa siempre el runtime embebido y evita depender de una instalacion global de Node.


## Problema comun: fallo con Python 3.14 y PySide6

Si aparece un error parecido a:

- `Could not find a version that satisfies the requirement PySide6==6.8.1`

significa que un pin estricto no coincide con los wheels disponibles para tu version de Python/plataforma.

### Solucion recomendada

1. Crear un entorno virtual limpio.
2. Actualizar `pip`.
3. Instalar dependencias desde `requirements.txt` actual (rangos compatibles).
4. Ejecutar el script de build.

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
./scripts/build_macos.sh x86_64 dist/macos-intel
```

Resultado esperado en Intel:

- `dist/macos-intel/ZPLConverter.app`
- `dist/macos-intel/ZPLConverter-x86_64.dmg`

## Builds locales

### Windows

```powershell
./scripts/build_windows.ps1
```

Salida esperada: `dist/windows/ZPLConverter/`

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

## CI/CD

El workflow `.github/workflows/build-multiplatform.yml` compila en:

- `windows-latest`
- `macos-13` (Intel)
- `macos-14` (Apple Silicon)

y sube artefactos separados por plataforma.

## Firma y notarizacion en macOS

Para distribuir fuera de desarrollo, agrega en una fase posterior:

1. Firma de `.app` con `codesign`.
2. Notarizacion con `notarytool`.
3. Staple del ticket (`xcrun stapler`).

Esto depende de certificados de Apple Developer y secretos en GitHub Actions.

## Notas sobre el runtime embebido de Node

El script `scripts/build_macos.sh` copia el binario real de `node` detectado en PATH hacia `renderer/runtime/node` antes de ejecutar PyInstaller. En macOS, ademas inspecciona las dependencias dinamicas de `node` con `otool -L` y copia las `.dylib` no pertenecientes al sistema dentro de `renderer/runtime/lib`. Como `pyinstaller/main.spec` empaqueta toda la carpeta `renderer`, el bundle final incluye ese runtime junto al renderer local.

En runtime, la app prepara `DYLD_LIBRARY_PATH` apuntando a `renderer/runtime/lib` cuando usa el Node embebido. Esto hace el bundle mas robusto que copiar solo el ejecutable de `node`, especialmente en instalaciones basadas en Homebrew.

Si necesitas omitir el runtime embebido o el DMG durante pruebas locales, ejecuta una de estas variantes:

```bash
EMBED_NODE_RUNTIME=0 ./scripts/build_macos.sh x86_64 dist/macos-intel
CREATE_DMG=0 ./scripts/build_macos.sh x86_64 dist/macos-intel
```
