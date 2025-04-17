from fastapi import APIRouter, Query, Request
from qqmusic_api import Credential
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from qqmusic_api.song import get_song_urls, SongFileType, get_detail, query_song
from qqmusic_api.lyric import get_lyric
from qqmusic_api.songlist import add_songs, del_songs
from qqmusic_api.user import get_created_songlist, get_fav_song

import asyncio

router = APIRouter()

br_map = {
    128000: SongFileType.MP3_128,
    192000: SongFileType.ACC_192,
    320000: SongFileType.MP3_320,
    350000: SongFileType.FLAC,
}


@router.get("/recommend")
async def recommend():
    return ResponseUtil.success([])


@router.get("/detail")
async def detail(request: Request, id: str = Query(...), br: int = Query(320000)):
    if not request.state.base_params.get("cookie"):
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential: Credential = request.state.base_params["cookie"]
    # 选择离用户最近的音质
    br = min(br_map.keys(), key=lambda x: abs(x - br))
    file_type = br_map[br]

    # 获取歌曲URL和详情
    url_result, detail_result, fav_result = await asyncio.gather(
        get_song_urls(mid=[id], file_type=file_type, credential=credential),
        get_detail(value=id),
        get_fav_song(euin=credential.encrypt_uin, credential=credential, num=2000)
    )
    fav_songs = fav_result.get("songlist", [])
    fav_song_ids = [song.get("mid") for song in fav_songs]
    url = url_result[id]
    # 获取文件大小
    file_size = 0
    if detail_result and "track_info" in detail_result:
        file_info = detail_result["track_info"].get("file", {})
        # 根据选择的音质获取对应的文件大小
        size_map = {
            128000: file_info.get("size_128mp3", 0),
            192000: file_info.get("size_192aac", 0),
            320000: file_info.get("size_320mp3", 0),
            350000: file_info.get("size_flac", 0)
        }
        file_size = size_map.get(br, 0)

    # 获取歌词
    lyric = await get_lyric(value=id, trans=True, roma=True)

    return ResponseUtil.success({
        "id": id,
        "meta": {
            "url": url,
            "size": file_size,
            "bitrate": br,
            "isFavorite": id in fav_song_ids,
            "lyric": {
                "normal": lyric.get("lyric", None),
                "translation": lyric.get("trans", None),
                "transliteration": lyric.get("roma", None)
            }
        }
    })


@router.put("/like")
async def like(request: Request, id: str = Query(...), like: bool = Query(True)):
    if not request.state.base_params.get("cookie"):
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential: Credential = request.state.base_params["cookie"]
    # 传入的id其实是mid，从mid反查id
    tracks = await query_song(value=[id])
    if not tracks:
        raise BusinessException("歌曲不存在", ErrorCode.SYSTEM_ERROR)
    raw_id = id
    id = tracks[0].get("id")
    if not id:
        raise BusinessException("歌曲不存在", ErrorCode.SYSTEM_ERROR)
    # 获取用户创建的歌单列表
    created_playlists = await get_created_songlist(uin=credential.str_musicid, credential=credential)
    if not created_playlists:
        raise BusinessException("获取创建的歌单失败", ErrorCode.SYSTEM_ERROR)
    # 从创建的歌单中获取第一个歌单的 dirid
    dirid = created_playlists[0].get("dirId")
    playlistId = created_playlists[0].get("tid")
    if not dirid:
        raise BusinessException("获取歌单ID失败", ErrorCode.SYSTEM_ERROR)
    # 根据操作添加或删除歌曲
    try:
        if like:
            await add_songs(dirid=dirid, song_ids=[
                int(id)], credential=credential)
        else:
            await del_songs(dirid=dirid, song_ids=[
                int(id)], credential=credential)
    except KeyError as e:
        if "result" in str(e):
            # 忽略 result 字段缺失的错误，因为接口实际上是成功的
            pass
        else:
            raise e

    return ResponseUtil.success({
        "id": raw_id,
        "like": like,
        "playlist": playlistId
    })
