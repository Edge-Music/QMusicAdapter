from fastapi import APIRouter
from app.api.v1.endpoints import health, connect, playlist, song, artist, search

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(connect.router, prefix="/connect", tags=["connect"])
api_router.include_router(playlist.router, prefix="/playlist", tags=["playlist"])
api_router.include_router(song.router, prefix="/song", tags=["song"])
api_router.include_router(artist.router, prefix="/artist", tags=["artist"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
