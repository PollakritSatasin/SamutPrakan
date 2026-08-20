from fastapi import APIRouter

from app.api.routes import cases, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cases.router, prefix="/api/v1/cases", tags=["cases"])
