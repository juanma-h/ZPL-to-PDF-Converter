# Arquitectura

## Vision general

La app se dividio en modulos pequenos para que la logica de negocio no dependa de la UI ni del empaquetado.

## Modulos principales

### `src/main.py`

Entry point minimo. Solo llama a `zpl_converter.app.main()`.

### `src/zpl_converter/app.py`

- crea `QApplication`
- registra metadatos de la app
- aplica una fuente apropiada por plataforma
- levanta la ventana principal

### `src/zpl_converter/models.py`

- constantes globales
- `ConversionConfig`
- `ConversionResult`
- `RuntimeStatus`
- `ZplDocumentStats`

### `src/zpl_converter/zpl_parser.py`

Responsable de inspeccionar el ZPL antes de convertir:

- separa etiquetas
- detecta `^PQ`
- calcula cantidad total estimada

Este modulo es puro y facil de probar.

### `src/zpl_converter/runtime.py`

Encapsula la deteccion de rutas de runtime:

- raiz en modo desarrollo
- raiz en modo PyInstaller
- renderer local
- `node` embebido
- variables de entorno para librerias dinamicas

### `src/zpl_converter/renderer.py`

Adaptador entre Python y el renderer Node:

- construye el comando
- ejecuta `render_zpl_local.mjs`
- interpreta la salida JSON
- convierte errores de subprocess a mensajes utiles para la app

### `src/zpl_converter/image_ops.py`

Postproceso de imagenes:

- unir PNG a PDF
- escribir metadata DPI
- composicion multicanal lado a lado

### `src/zpl_converter/conversion.py`

Orquestador principal del flujo:

- valida entrada
- analiza ZPL
- llama al renderer
- decide PNG o PDF
- usa staging temporal controlado por la app

La intencion es que este modulo pueda reutilizarse fuera de Qt.

### `src/zpl_converter/ui/`

Contiene la capa visual:

- `theme.py`: stylesheet y sombras
- `widgets.py`: tarjetas, tiles y drag-and-drop
- `main_window.py`: layout, `QSettings`, acciones de usuario y worker Qt

## Flujo de conversion

1. Usuario selecciona archivo y configuracion.
2. La UI analiza el ZPL y actualiza el resumen en vivo.
3. La conversion corre en un `QThread`.
4. Python invoca Node para generar PNG base.
5. Si aplica, Python recompone multicanal.
6. Si aplica, Python genera el PDF final.
7. La UI muestra resultado y puede abrir la salida.

## Compatibilidad multiplataforma

- Windows: puede embeber `node.exe` dentro del bundle
- macOS: puede embeber `node` y sus dependencias dinamicas
- CI: usa los scripts reales del repo para evitar diferencias entre local y GitHub Actions

## Pruebas

La cobertura actual se enfoca en piezas puras:

- parsing de ZPL
- parseo de salida del renderer
- composicion de imagenes

La UI y los builds se validan con smoke tests manuales o de entorno.
