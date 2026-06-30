# Arquitectura web

## Principios

- Backend y frontend tienen dependencias, pruebas y ciclos de desarrollo separados.
- La logica ZPL no depende de FastAPI ni de React.
- El navegador nunca controla rutas del sistema de archivos del servidor.
- Los trabajos de conversion usan espacios temporales aislados y eliminables.
- El renderer sigue siendo local: la aplicacion no envia ZPL a terceros.

## Flujo

```text
React
  -> POST multipart/form-data
FastAPI API
  -> valida y crea workspace temporal
Conversion service
  -> Node.js + zpl-renderer-js
  -> PNG base
  -> composicion y metadatos con Pillow
  -> PDF o ZIP
FastAPI FileResponse
  -> descarga
  -> limpieza del workspace
```

## Backend

### `api/`

Define contratos HTTP, validacion de formularios, respuestas y codigos de error. No contiene algoritmos de renderizado.

### `domain/`

Contiene las estructuras `ConversionConfig`, `ConversionResult`, `RuntimeStatus` y `ZplDocumentStats`.

### `services/`

- `zpl_parser.py`: separacion de etiquetas y lectura de `^PQ`.
- `runtime.py`: localizacion multiplataforma de Node.js.
- `renderer.py`: ejecucion controlada del proceso Node.
- `image_ops.py`: PDF, DPI y composicion multicanal.
- `conversion.py`: orquestacion del caso de uso.

## Frontend

React organiza la pantalla en componentes independientes. TypeScript tipa los contratos compartidos en el cliente, mientras `api/client.ts` concentra toda comunicacion HTTP. El hook `useZplConverter` coordina estados de analisis, conversion, error y descarga.

## Produccion

El build de Vite produce archivos estaticos en `frontend/dist`. La imagen Docker copia ese resultado y FastAPI lo sirve en `/`, manteniendo API y frontend bajo el mismo origen.
