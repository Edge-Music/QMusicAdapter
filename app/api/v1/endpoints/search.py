from fastapi import APIRouter, Query, Request
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from qqmusic_api import Client, Credential
from qqmusic_api.modules.search import SearchType
from app.common.types.playlist import convert_qq_song


router = APIRouter()


@router.get("/")
async def search(request: Request, keywords: str = Query(...), limit: int = Query(10)):
    cookie_dict = request.state.base_params.get("cookie")
    if not cookie_dict:
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential = Credential.model_validate(cookie_dict)
    try:
        async with Client(credential=credential) as client:
            result = await client.search.search_by_type(
                keyword=keywords,
                num=limit,
                search_type=SearchType.SONG,
                highlight=False,
            )
            songs = (
                [convert_qq_song(song) for song in result.song] if result.song else []
            )
            return ResponseUtil.success({"songs": songs})
    except Exception as e:
        raise BusinessException(f"搜索失败: {str(e)}", ErrorCode.SYSTEM_ERROR)
