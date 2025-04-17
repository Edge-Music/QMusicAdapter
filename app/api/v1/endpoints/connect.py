from fastapi import APIRouter, Query, Request
from qqmusic_api import Credential
from app.services.qq_music import QQMusicService
from app.utils.cache import MemoryCache
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from qqmusic_api.user import get_homepage

router = APIRouter()


@router.get("/qr/key")
async def qr_key():
    qr_data = await QQMusicService.get_qr_key()
    # 缓存二维码数据
    MemoryCache.set(qr_data["identifier"], qr_data)
    return ResponseUtil.success({
        "unikey": qr_data["identifier"],
        "qr_data": qr_data["data"],
        "mimetype": qr_data["mimetype"]
    })


@router.get("/qr/create")
async def qr_create(key: str = Query(...), qrimg: bool = Query(True)):
    qr_data = MemoryCache.get(key)
    if not qr_data:
        raise BusinessException("二维码已过期", ErrorCode.PARAM_ERROR)

    return ResponseUtil.success({
        "qrurl": qr_data["data"],
        "qrimg": f"data:{qr_data['mimetype']};base64,{qr_data['data']}" if qrimg else None
    })


@router.get("/qr/check")
async def qr_check(key: str = Query(...)):
    qr_data = MemoryCache.get(key)
    if not qr_data:
        raise BusinessException("二维码已过期", ErrorCode.PARAM_ERROR)

    status, cookie = await QQMusicService.check_qr_status(qr_data)
    if status == 2:  # 登录成功
        MemoryCache.delete(key)

    return ResponseUtil.success({
        "status": status,
        "cookie": cookie.as_json() if cookie else None
    })


@router.get("/status")
async def status(request: Request):
    if not request.state.base_params.get("cookie"):
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential: Credential = request.state.base_params["cookie"]
    try:
        result = await get_homepage(credential.encrypt_uin, credential=credential)
        if result is None:
            raise BusinessException("获取用户信息失败", ErrorCode.SYSTEM_ERROR)
        info = result['Info']['BaseInfo']
        result = {
            "id": credential.musicid,
            "name": info['Name'],
            "avatar": info['Avatar']
        }
        return ResponseUtil.success(result)
    except Exception as e:
        raise BusinessException(f"获取用户信息失败: {str(e)}", ErrorCode.SYSTEM_ERROR)
