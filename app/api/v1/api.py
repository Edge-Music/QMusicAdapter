from fastapi import APIRouter
from app.api.v1.endpoints import health, connect, playlist, song, artist, search


def register_api_routes(router: APIRouter):
    router.include_router(health.router)
    router.include_router(connect.router, prefix="/connect", tags=["connect"])
    router.include_router(playlist.router, prefix="/playlist", tags=["playlist"])
    router.include_router(song.router, prefix="/song", tags=["song"])
    router.include_router(artist.router, prefix="/artist", tags=["artist"])
    router.include_router(search.router, prefix="/search", tags=["search"])


api_router = APIRouter()

qq_router = APIRouter(prefix="/qq", tags=["qq"])
register_api_routes(qq_router)
api_router.include_router(qq_router)

wechat_router = APIRouter(prefix="/wechat", tags=["wechat"])
register_api_routes(wechat_router)
api_router.include_router(wechat_router)
