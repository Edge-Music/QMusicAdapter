from fastapi import APIRouter
from app.utils.helpers import ResponseUtil

router = APIRouter()

@router.get("/recommend")
async def recommend():
    return ResponseUtil.success([])