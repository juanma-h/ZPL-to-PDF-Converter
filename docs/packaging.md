# Packaging multiplataforma

## Objetivo

Mantener una sola base de codigo para:

- Windows x64
- macOS Intel
- macOS Apple Silicon

## Pieza clave

El bundle incluye la carpeta `renderer/`, de modo que la app distribuida conserve:

- `render_zpl_local.mjs`
- `node_modules/zpl-renderer-js`
- runtime de Node embebido cuando el build lo prepara

Eso se define en [pyinstaller/main.spec](../pyinstaller/main.spec).

## Windows

El script [scripts/build_windows.ps1](../scripts/build_windows.ps1):

1. prepara caches de `pip` y `PyInstaller`
2. detecta `node.exe` en PATH
3. copia `node.exe` y DLL vecinas a `renderer/runtime/`
4. ejecuta `PyInstaller`

Resultado esperado:

- `dist/windows/ZPLConverter/`

## macOS

El script [scripts/build_macos.sh](../scripts/build_macos.sh):

1. detecta el binario real de `node`
2. copia `renderer/runtime/node`
3. inspecciona dependencias con `otool -L`
4. copia `.dylib` externas a `renderer/runtime/lib`
5. ejecuta `PyInstaller`
6. genera `.dmg` cuando `CREATE_DMG=1`

Resultados esperados:

- `dist/macos-*/ZPLConverter.app`
- `dist/macos-*/ZPLConverter-<arch>.dmg`

## CI

El workflow [build-multiplatform.yml](../.github/workflows/build-multiplatform.yml) ya no llama a `PyInstaller` directo. Ahora usa los scripts del repo:

- Windows: `build_windows.ps1`
- macOS: `build_macos.sh`

Eso evita diferencias entre artefactos de CI y builds locales.

## Variables de build

### Compartidas por los scripts

- `SKIP_PYTHON_DEPS_INSTALL=1`
- `SKIP_NPM_INSTALL=1`
- `STRICT_EMBED_NODE_RUNTIME=1`
- `EMBED_NODE_RUNTIME=0`

### Solo macOS

- `CREATE_DMG=0`

## Runtime y fallback

En ejecucion, la app intenta:

1. `renderer/runtime/node(.exe)`
2. `node` desde PATH

Si ninguno existe, falla con un mensaje claro.

## Firma y notarizacion en macOS

El repo aun no firma ni notariza automaticamente. Para distribucion publica fuera de desarrollo faltaria:

1. `codesign` del `.app`
2. notarizacion con `notarytool`
3. `stapler`

## Recomendacion

Para distribuir a usuarios finales:

- en Windows: usa `STRICT_EMBED_NODE_RUNTIME=1`
- en macOS: usa `STRICT_EMBED_NODE_RUNTIME=1`

Asi el bundle no depende de un Node instalado manualmente.
