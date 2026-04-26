from fastapi import APIRouter, Query, Request
from qqmusic_api import Client, Credential
from qqmusic_api.modules.song import SongFileType, SongFileInfo
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode

import asyncio

router = APIRouter()

br_map = {
    128000: SongFileType.MP3_128,
    192000: SongFileType.ACC_192,
    320000: SongFileType.MP3_320,
    350000: SongFileType.FLAC,
}

FALLBACK_ORDER = [350000, 320000, 192000, 128000]


@router.get("/recommend")
async def recommend():
    return ResponseUtil.success([])


async def _get_song_url(client, mid: str, file_type: SongFileType, credential: Credential) -> str:
    resp = await client.song.get_song_urls(
        [SongFileInfo(mid=mid)], file_type=file_type, credential=credential
    )
    if resp.data and resp.data[0].purl:
        cdn = await client.song.get_cdn_dispatch()
        if cdn.sip:
            return cdn.sip[0] + resp.data[0].purl
        return f"https://ws.stream.qqmusic.qq.com/{resp.data[0].purl}"
    return ""


@router.get("/detail")
async def detail(request: Request, id: str = Query(...), br: int = Query(320000)):
    cookie_dict = request.state.base_params.get("cookie")
    if not cookie_dict:
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential = Credential.model_validate(cookie_dict)
    br = min(br_map.keys(), key=lambda x: abs(x - br))
    file_type = br_map[br]

    async with Client(credential=credential) as client:
        detail_result, fav_result = await asyncio.gather(
            asyncio.ensure_future(client.song.get_detail(value=id)),
            asyncio.ensure_future(client.user.get_fav_song(euin=credential.encrypt_uin, num=2000)),
        )

        fav_song_ids = (
            [song.mid for song in fav_result.songs] if fav_result.songs else []
        )

        url = await _get_song_url(client, id, file_type, credential)

        if not url:
            for fallback_br in FALLBACK_ORDER:
                if fallback_br == br:
                    continue
                url = await _get_song_url(client, id, br_map[fallback_br], credential)
                if url:
                    br = fallback_br
                    break

        file_size = 0
        if detail_result and detail_result.track and detail_result.track.file:
            file_info = detail_result.track.file
            size_map = {
                128000: file_info.size_128mp3,
                192000: file_info.size_192aac,
                320000: file_info.size_320mp3,
                350000: file_info.size_flac,
            }
            file_size = size_map.get(br, 0)

        lyric_resp = await client.lyric.get_lyric(value=id, trans=True, roma=True)
        lyric = lyric_resp.decrypt() if lyric_resp.crypt == 1 else lyric_resp

        return ResponseUtil.success(
            {
                "id": id,
                "meta": {
                    "url": url,
                    "size": file_size,
                    "bitrate": br,
                    "isFavorite": id in fav_song_ids,
                    "lyric": {
                        "normal": lyric.lyric if lyric else None,
                        "translation": lyric.trans if lyric else None,
                        "transliteration": lyric.roma if lyric else None,
                    },
                },
            }
        )


@router.put("/like")
async def like(request: Request, id: str = Query(...), like: bool = Query(True)):
    cookie_dict = request.state.base_params.get("cookie")
    if not cookie_dict:
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential = Credential.model_validate(cookie_dict)

    async with Client(credential=credential) as client:
        tracks = await client.song.query_song(value=[id])

        if not tracks or not tracks.tracks:
            raise BusinessException("歌曲不存在", ErrorCode.SYSTEM_ERROR)

        raw_id = id
        song_id = tracks.tracks[0].id
        song_type = tracks.tracks[0].type or 0

        if not song_id:
            raise BusinessException("歌曲不存在", ErrorCode.SYSTEM_ERROR)

        created_playlists = await client.user.get_created_songlist(
            uin=int(credential.str_musicid)
        )

        if not created_playlists or not created_playlists.playlists:
            raise BusinessException("获取创建的歌单失败", ErrorCode.SYSTEM_ERROR)

        dirid = created_playlists.playlists[0].dirid
        playlist_id = created_playlists.playlists[0].id

        if not dirid:
            raise BusinessException("获取歌单ID失败", ErrorCode.SYSTEM_ERROR)

        try:
            if like:
                await client.songlist.add_songs(
                    dirid=dirid, song_info=[(song_id, song_type)], credential=credential
                )
            else:
                await client.songlist.del_songs(
                    dirid=dirid, song_info=[(song_id, song_type)], credential=credential
                )
        except Exception:
            pass

        return ResponseUtil.success(
            {"id": raw_id, "like": like, "playlist": playlist_id}
        )