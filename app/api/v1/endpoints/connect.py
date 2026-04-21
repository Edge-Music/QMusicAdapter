from fastapi import APIRouter, Query, Request, Depends
from qqmusic_api import Client, Credential
from qqmusic_api.models.login import QRLoginType
from app.services.qq_music import QQMusicService
from app.utils.cache import MemoryCache
from app.utils.helpers import ResponseUtil
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode

router = APIRouter()


def get_login_type(request: Request) -> QRLoginType:
    path = request.url.path
    if "/wechat" in path:
        return QRLoginType.WX
    return QRLoginType.QQ


@router.get("/qr/key")
async def qr_key(request: Request, login_type: QRLoginType = Depends(get_login_type)):
    qr_data = await QQMusicService.get_qr_key(login_type)
    MemoryCache.set(qr_data["identifier"], qr_data)
    return ResponseUtil.success(
        {
            "unikey": qr_data["identifier"],
            "qr_data": qr_data["data"],
            "mimetype": qr_data["mimetype"],
        }
    )


@router.get("/qr/create")
async def qr_create(key: str = Query(...), qrimg: bool = Query(True)):
    qr_data = MemoryCache.get(key)
    if not qr_data:
        raise BusinessException("二维码已过期", ErrorCode.PARAM_ERROR)

    return ResponseUtil.success(
        {
            "qrurl": qr_data["data"],
            "qrimg": f"data:{qr_data['mimetype']};base64,{qr_data['data']}"
            if qrimg
            else None,
        }
    )


@router.get("/qr/check")
async def qr_check(key: str = Query(...)):
    qr_data = MemoryCache.get(key)
    if not qr_data:
        raise BusinessException("二维码已过期", ErrorCode.PARAM_ERROR)

    status, cookie = await QQMusicService.check_qr_status(qr_data)
    if status == 2:
        MemoryCache.delete(key)

    return ResponseUtil.success({"status": status, "cookie": cookie})


@router.get("/status")
async def status(request: Request):
    cookie_dict = request.state.base_params.get("cookie")
    if not cookie_dict:
        raise BusinessException("请先登录", ErrorCode.UNAUTHORIZED)

    credential = Credential.model_validate(cookie_dict)
    try:
        async with Client(credential=credential) as client:
            result = await client.user.get_homepage(credential.encrypt_uin)
            result_data = await result
            if result_data is None:
                raise BusinessException("获取用户信息失败", ErrorCode.SYSTEM_ERROR)
            info = result_data.info.base_info
            return ResponseUtil.success(
                {
                    "id": credential.musicid,
                    "name": info.name,
                    "avatar": info.avatar,
                }
            )
    except Exception as e:
        raise BusinessException(f"获取用户信息失败: {str(e)}", ErrorCode.SYSTEM_ERROR)
