from fastapi import APIRouter, Query, Request
from qqmusic_api import Client, Credential
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from app.common.types.playlist import convert_qq_playlist, convert_qq_playlist_detail

import asyncio

router = APIRouter()


@router.get("/list")
async def list(request: Request, limit: int = Query(1000)):
    cookie_dict = request.state.base_params.get("cookie")
    if not cookie_dict:
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential = Credential.model_validate(cookie_dict)
    try:
        async with Client(credential=credential) as client:
            created_playlists_resp, fav_playlists_resp = await asyncio.gather(
                client.user.get_created_songlist(uin=int(credential.str_musicid)),
                client.user.get_fav_songlist(euin=credential.encrypt_uin, num=limit),
            )
            created_playlists = await created_playlists_resp
            fav_playlists_data = await fav_playlists_resp

            all_playlists = created_playlists.playlists + (
                fav_playlists_data.playlists if fav_playlists_data.playlists else []
            )

            async def get_playlist_detail(playlist):
                try:
                    detail_resp = client.songlist.get_detail(
                        songlist_id=playlist.id, num=1, tag=False
                    )
                    detail = await detail_resp
                    if detail and detail.dirinfo:
                        creator_info = detail.dirinfo.creator
                        playlist_data = playlist.model_dump()
                        playlist_data["creator"] = {
                            "id": str(creator_info.musicid) if creator_info else "",
                            "name": creator_info.nick if creator_info else None,
                            "avatar": creator_info.headurl if creator_info else None,
                        }
                        return playlist_data
                except Exception:
                    pass
                return playlist.model_dump()

            detailed_playlists = await asyncio.gather(
                *[get_playlist_detail(playlist) for playlist in all_playlists]
            )

            converted_playlists = [
                convert_qq_playlist(playlist) for playlist in detailed_playlists
            ]

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
    cookie_dict = request.state.base_params.get("cookie")
    if not cookie_dict:
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential = Credential.model_validate(cookie_dict)
    async with Client(credential=credential) as client:
        result_resp = client.songlist.get_detail(
            songlist_id=id, num=2000, onlysong=False, tag=False, userinfo=False
        )
        result = await result_resp
        converted_result = await convert_qq_playlist_detail(
            result.model_dump(), credential
        )
        return ResponseUtil.success(converted_result)
