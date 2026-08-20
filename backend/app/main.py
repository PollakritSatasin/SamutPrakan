from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.db import init_db
from app.services.state_manager import SessionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.session_manager = SessionManager()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Simulated Patient training API",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
