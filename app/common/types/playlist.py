from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum
import asyncio
from qqmusic_api import Credential
from qqmusic_api.album import get_cover

class PlaylistType(str, Enum):
    NORMAL = "normal"
    ALBUM = "album"
    DJ = "dj"
    ARTIST = "artist"

class User(BaseModel):
    id: str
    name: Optional[str] = None
    avatar: Optional[str] = None

class Privilege(BaseModel):
    playable: bool
    reason: Optional[str] = None
    bitrates: Optional[List[int]] = None
    maxBitrate: Optional[int] = None

class Lyric(BaseModel):
    normal: Optional[str] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None

class SongMeta(BaseModel):
    url: Optional[str] = None
    isFavorite: Optional[bool] = None
    lyric: Optional[Lyric] = None

class Artist(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None

class Album(BaseModel):
    id: str
    name: str
    cover: Optional[str] = None
    artists: Optional[List[Artist]] = None
    size: Optional[int] = None

class Song(BaseModel):
    id: str
    name: Optional[str] = None
    tns: Optional[List[str]] = None
    artists: Optional[List[Artist]] = None
    album: Optional[Album] = None
    duration: Optional[int] = None
    privilege: Optional[Privilege] = None
    meta: Optional[SongMeta] = None

class Playlist(BaseModel):
    id: str
    name: Optional[str] = None
    cover: Optional[str] = None
    size: Optional[int] = None
    creator: Optional[User] = None
    songs: Optional[List[Song]] = None
    type: Optional[PlaylistType] = PlaylistType.NORMAL
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

def convert_qq_playlist(raw_playlist: Dict[str, Any]) -> Playlist:
    """将QQ音乐API返回的原始歌单数据转换为标准Playlist格式"""
    creator = None
    if "creator" in raw_playlist:
        creator_info = raw_playlist["creator"]
        creator = User(
            id=str(creator_info.get("id", "")),
            name=creator_info.get("name"),
            avatar=creator_info.get("avatar")
        )
    elif "uin" in raw_playlist:
        creator = User(
            id=str(raw_playlist.get("uin", "")),
            name=raw_playlist.get("nickname"),
            avatar=None
        )

    return Playlist(
        id=str(raw_playlist.get("tid", "")),
        name=raw_playlist.get("dirName") or raw_playlist.get("name"),
        cover=raw_playlist.get("picUrl") or raw_playlist.get("logo"),
        size=raw_playlist.get("songNum") or raw_playlist.get("songnum"),
        creator=creator,
        type=PlaylistType.NORMAL,
        description=None,
        meta={
            "dirId": raw_playlist.get("dirId"),
            "createTime": raw_playlist.get("createTime") or raw_playlist.get("createtime"),
            "updateTime": raw_playlist.get("updateTime"),
            "status": raw_playlist.get("status"),
            "sortWeight": raw_playlist.get("sortWeight"),
            "orderTime": raw_playlist.get("orderTime")
        }
    )

async def convert_qq_song(raw_song: Dict[str, Any]) -> Song:
    """将QQ音乐API返回的原始歌曲数据转换为标准Song格式"""
    # 处理权限信息TODO:暂时不清楚如何判断是否可播放
    pay_info = raw_song.get("pay", {})
    playable = pay_info.get("pay_play", 1) == 0
    
    # 处理码率信息
    bitrates = []
    max_bitrate = 0
    file_info = raw_song.get("file", {})
    
    # 定义码率映射
    bitrate_map = {
        "size_128mp3": 128000,
        "size_192aac": 192000,
        "size_320mp3": 320000,
        "size_flac": 350000
    }
    
    # 检查每个码率是否可用
    for size_key, bitrate in bitrate_map.items():
        if file_info.get(size_key, 0) > 0:
            bitrates.append(bitrate)
            max_bitrate = max(max_bitrate, bitrate)
    
    # 处理歌手信息
    artists = []
    for singer in raw_song.get("singer", []):
        artists.append(Artist(
            id=str(singer.get("mid", "")),
            name=singer.get("name", ""),
            avatar=None
        ))
    
    # 处理专辑信息
    album_info = raw_song.get("album", {})
    album = None
    if album_info:
        album = Album(
            id=str(album_info.get("mid", "")),
            name=album_info.get("name", ""),
            cover=get_cover(album_info.get("mid", ""), 300),
            artists=artists
        )
    
    # 构建权限信息
    privilege = Privilege(
        playable=True,
        bitrates=bitrates if bitrates else None,
        maxBitrate=max_bitrate if max_bitrate > 0 else None
    )
    
    return Song(
        id=str(raw_song.get("mid", "")),
        name=raw_song.get("name", ""),
        tns=[raw_song.get("subtitle")] if raw_song.get("subtitle") else None,
        artists=artists,
        album=album,
        duration=raw_song.get("interval") * 1000,
        privilege=privilege,
        meta={
            "url": raw_song.get("url", ""),
            "isFavorite": False,
            "lyric": None
        }
    )

async def convert_qq_playlist_detail(raw_playlist: Dict[str, Any], credential: Credential) -> Dict[str, Any]:
    """将QQ音乐API返回的歌单详情数据转换为标准Playlist格式"""
    songs = []
    if "songlist" in raw_playlist:
        # 并发转换所有歌曲
        songs = await asyncio.gather(*[convert_qq_song(song) for song in raw_playlist["songlist"]])
        
        # 获取所有专辑封面
        album_covers = {}
        for song in songs:
            if song.album and song.album.id:
                try:
                    if song.album.id not in album_covers:
                        cover_url = get_cover(song.album.id, 300)
                        album_covers[song.album.id] = cover_url
                except Exception as e:
                    print(e)
        
        # 更新歌曲的专辑封面
        for song in songs:
            if song.album and song.album.id in album_covers:
                song.album.cover = album_covers[song.album.id]
    
    return {
        "id": str(raw_playlist.get("dirinfo", {}).get("id", "")),
        "songs": songs
    }