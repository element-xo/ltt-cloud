from fastapi import APIRouter

from ltt_core.config import get_settings

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "environment": settings.ENVIRONMENT}