# ZPL Converter Web

Aplicacion web para convertir documentos ZPL a PDF o paquetes PNG mediante un renderer local. El repositorio usa una arquitectura monorepo con backend y frontend independientes.

## Arquitectura

```text
.
|-- backend/                 # API FastAPI y logica de negocio
|   `-- app/
|       |-- api/             # Endpoints y contratos HTTP
|       |-- core/            # Configuracion y errores compartidos
|       |-- domain/          # Modelos de dominio
|       `-- services/        # Parser, renderer, imagenes y conversion
|-- frontend/                # React + TypeScript + Vite
|   `-- src/
|       |-- api/             # Cliente HTTP
|       |-- components/      # Componentes visuales
|       |-- hooks/           # Estado y casos de uso de la interfaz
|       |-- styles/          # Sistema visual responsive
|       `-- types/           # Contratos TypeScript
|-- renderer/                # Adaptador Node.js para zpl-renderer-js
|-- tests/                   # Pruebas del backend
|-- Dockerfile               # Imagen de produccion
`-- compose.yaml             # Ejecucion local en contenedor
```

La logica de parsing, renderizado, composicion y generacion de PDF se conserva en `backend/app/services`. La API adapta las rutas locales de la antigua aplicacion desktop a cargas y descargas HTTP.

## Requisitos

- Python 3.11+
- Node.js 22+
- npm 10+

## Desarrollo local

### 1. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"

cd renderer
npm ci
cd ..

uvicorn backend.app.main:app --reload
```

API: <http://127.0.0.1:8000/api/v1/docs>

### 2. Frontend

En otra terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Aplicacion: <http://localhost:5173>

Vite redirige `/api` hacia el backend durante desarrollo.

## Pruebas y calidad

```powershell
python -m pytest
ruff check backend tests

cd frontend
npm run lint
npm run build
```

## Produccion con Docker

```powershell
docker compose up --build
```

La aplicacion queda disponible en <http://localhost:8000>. La imagen compila React, instala el renderer Node y sirve el frontend desde FastAPI.

## Variables de entorno

Copia `.env.example` a `.env` si necesitas cambiar los valores:

- `MAX_UPLOAD_BYTES`: tamaño maximo del archivo recibido.
- `MAX_RENDERED_LABELS`: cantidad maxima de etiquetas por solicitud.
- `RENDERER_TIMEOUT_SECONDS`: timeout del proceso Node.
- `CORS_ORIGINS`: origenes permitidos, separados por coma.
- `NODE_BINARY`: ruta opcional a un ejecutable Node especifico.

## Endpoints

- `GET /api/v1/health`: estado de API y renderer.
- `POST /api/v1/zpl/analyze`: analiza etiquetas y comandos `^PQ`.
- `POST /api/v1/zpl/convert`: devuelve un PDF o ZIP con imágenes PNG.

Los archivos se procesan en un directorio temporal del servidor y se eliminan después de enviar la respuesta.

## Documentacion

- [Arquitectura](./docs/architecture.md)
- OpenAPI interactivo: `/api/v1/docs`
