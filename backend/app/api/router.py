from fastapi import APIRouter

from .routes import health, zpl

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(zpl.router)
