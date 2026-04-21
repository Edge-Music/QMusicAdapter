from fastapi import APIRouter
from app.utils.helpers import ResponseUtil

router = APIRouter()


@router.get("/health")
async def health_check():
    return ResponseUtil.success({"status": "healthy"})
