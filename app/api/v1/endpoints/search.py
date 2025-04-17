from fastapi import APIRouter, Query, Request
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from qqmusic_api import Credential
from qqmusic_api.search import search_by_type, SearchType
from app.common.types.playlist import convert_qq_song
import asyncio


router = APIRouter()

@router.get("/")
async def search(request: Request, keywords: str = Query(...), limit: int = Query(10)):
    if not request.state.base_params.get("cookie"):
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential: Credential = request.state.base_params["cookie"]
    try:
        result = await search_by_type(keyword=keywords, num=limit, credential=credential, highlight=False, search_type=SearchType.SONG)
        songs = await asyncio.gather(*[convert_qq_song(song) for song in result])
        return ResponseUtil.success({
          "songs": songs
        })
    except Exception as e:
        raise BusinessException(f"搜索失败: {str(e)}", ErrorCode.SYSTEM_ERROR)
