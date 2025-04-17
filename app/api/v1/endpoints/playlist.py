from fastapi import APIRouter, Query, Request
from qqmusic_api import Credential
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from app.common.types.playlist import convert_qq_playlist, convert_qq_playlist_detail
from qqmusic_api.user import get_created_songlist, get_fav_songlist
from qqmusic_api.songlist import get_detail 

import asyncio

router = APIRouter()


@router.get("/list")
async def list(request: Request, limit: int = Query(1000)):
    if not request.state.base_params.get("cookie"):
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential: Credential = request.state.base_params["cookie"]
    try:
        # 并发请求两个歌单列表
        created_playlists, fav_playlists = await asyncio.gather(
            get_created_songlist(uin=credential.str_musicid, credential=credential),
            get_fav_songlist(euin=credential.encrypt_uin, credential=credential, num=limit)
        )
        # 合并并转换所有歌单数据为标准格式
        all_playlists = created_playlists + fav_playlists.get("v_list", [])
        
        # 获取每个歌单的详细信息
        async def get_playlist_detail(playlist):
            try:
                detail = await get_detail(songlist_id=playlist.get("tid"), num=1, tag=False)
                if detail and "dirinfo" in detail:
                    creator_info = detail["dirinfo"].get("creator", {})
                    playlist["creator"] = {
                        "id": str(creator_info.get("musicid", "")),
                        "name": creator_info.get("nick"),
                        "avatar": creator_info.get("headurl")
                    }
                
            except Exception:
                pass
            return playlist

        # 并发获取所有歌单的详细信息
        detailed_playlists = await asyncio.gather(*[get_playlist_detail(playlist) for playlist in all_playlists])
        
        # 转换为标准格式
        converted_playlists = [convert_qq_playlist(playlist) for playlist in detailed_playlists]
        
        return ResponseUtil.success(converted_playlists)
    except Exception as e:
        raise BusinessException(f"获取用户信息失败: {str(e)}", ErrorCode.SYSTEM_ERROR)


@router.get("/recommend")
async def recommend():
    return ResponseUtil.success([])

@router.get("/toplist")
async def toplist():
    return ResponseUtil.success([])
    

@router.get("/detail")
async def detail(request: Request, id: int = Query(...)):
    if not request.state.base_params.get("cookie"):
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)
        
    credential: Credential = request.state.base_params["cookie"]
    result = await get_detail(songlist_id=id, num=2000, onlysong=False, tag=False, userinfo=False)
    converted_result = await convert_qq_playlist_detail(result, credential)
    return ResponseUtil.success(converted_result)




