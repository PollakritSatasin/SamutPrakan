from fastapi import APIRouter

from app.api.v1 import cases, sessions

router = APIRouter(prefix="/api/v1")
router.include_router(cases.router, prefix="/cases", tags=["cases"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
