from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api.router import api_router
from .core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=__version__,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=None,
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Generated-Files", "X-Rendered-Labels"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.include_router(api_router, prefix=settings.api_prefix)

if settings.frontend_dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.frontend_dist_dir, html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def root() -> JSONResponse:
        return JSONResponse(
            {
                "name": settings.app_name,
                "version": __version__,
                "message": "Frontend no compilado. Ejecuta npm run build en frontend/.",
            }
        )
