from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum
import asyncio
from qqmusic_api import Credential
from qqmusic_api.models.base import Song, Singer, Album as QqAlbum


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


class SongItem(BaseModel):
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
    songs: Optional[List[SongItem]] = None
    type: Optional[PlaylistType] = PlaylistType.NORMAL
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def convert_qq_playlist(raw_playlist: Dict[str, Any]) -> Playlist:
    creator = None
    if "creator" in raw_playlist:
        creator_info = raw_playlist["creator"]
        creator = User(
            id=str(creator_info.get("id", "")),
            name=creator_info.get("name"),
            avatar=creator_info.get("avatar"),
        )
    elif "uin" in raw_playlist:
        creator = User(
            id=str(raw_playlist.get("uin", "")),
            name=raw_playlist.get("nickname"),
            avatar=None,
        )

    return Playlist(
        id=str(raw_playlist.get("id", "")) or str(raw_playlist.get("tid", "")),
        name=raw_playlist.get("title")
        or raw_playlist.get("dirName")
        or raw_playlist.get("name"),
        cover=raw_playlist.get("picurl")
        or raw_playlist.get("picUrl")
        or raw_playlist.get("logo"),
        size=raw_playlist.get("songnum") or raw_playlist.get("songNum"),
        creator=creator,
        type=PlaylistType.NORMAL,
        description=raw_playlist.get("desc"),
        meta={
            "dirId": raw_playlist.get("dirid") or raw_playlist.get("dirId"),
            "createTime": raw_playlist.get("createTime")
            or raw_playlist.get("createtime"),
            "updateTime": raw_playlist.get("updateTime"),
        },
    )


def convert_qq_song(raw_song: Song) -> SongItem:
    artists = []
    if raw_song.singer:
        for singer in raw_song.singer:
            artists.append(
                Artist(
                    id=singer.mid or "",
                    name=singer.name or "",
                    avatar=singer.cover_url() if singer.mid else None,
                )
            )

    album = None
    if raw_song.album:
        album = Album(
            id=raw_song.album.mid or "",
            name=raw_song.album.name or "",
            cover=raw_song.album.cover_url() if raw_song.album.mid else None,
            artists=artists,
        )

    bitrates = []
    max_bitrate = 0
    if raw_song.file:
        file_info = raw_song.file
        bitrate_map = {
            "size_128mp3": 128000,
            "size_192aac": 192000,
            "size_320mp3": 320000,
            "size_flac": 350000,
        }
        for attr, bitrate in bitrate_map.items():
            if getattr(file_info, attr, 0) > 0:
                bitrates.append(bitrate)
                max_bitrate = max(max_bitrate, bitrate)

    privilege = Privilege(
        playable=True,
        bitrates=bitrates if bitrates else None,
        maxBitrate=max_bitrate if max_bitrate > 0 else None,
    )

    return SongItem(
        id=raw_song.mid or "",
        name=raw_song.name or "",
        tns=[raw_song.subtitle] if raw_song.subtitle else None,
        artists=artists,
        album=album,
        duration=(raw_song.interval or 0) * 1000,
        privilege=privilege,
        meta=SongMeta(url="", isFavorite=False, lyric=None),
    )


async def convert_qq_playlist_detail(
    raw_playlist: Dict[str, Any], credential: Credential
) -> Dict[str, Any]:
    songs = []
    if "songs" in raw_playlist:
        songs = [convert_qq_song(song) for song in raw_playlist["songs"]]

    dirinfo = raw_playlist.get("dirinfo", {})
    return {"id": str(dirinfo.get("id", "")), "songs": songs}
