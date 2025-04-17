from qqmusic_api import Credential
from qqmusic_api.login import QR, QRLoginType, get_qrcode, check_qrcode, QRCodeLoginEvents
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
import base64


class QQMusicService:
    @staticmethod
    async def get_qr_key(type: QRLoginType = QRLoginType.QQ) -> dict:
        try:
            qr = await get_qrcode(type)
            # 将二进制数据转换为base64
            qr_base64 = base64.b64encode(qr.data).decode('utf-8')
            return {
                "data": qr_base64,
                "qr_type": qr.qr_type,
                "mimetype": qr.mimetype,
                "identifier": qr.identifier
            }
        except Exception as e:
            raise BusinessException(
                f"获取二维码失败: {str(e)}", ErrorCode.SYSTEM_ERROR)

    @staticmethod
    async def check_qr_status(qr_data: dict) -> tuple[int, Credential]:
        try:
            # 创建 QR 对象
            qr = QR(
                data=base64.b64decode(qr_data["data"]),
                qr_type=qr_data["qr_type"],
                mimetype=qr_data["mimetype"],
                identifier=qr_data["identifier"]
            )

            event, credential = await check_qrcode(qr)
            status = -1  # 默认过期

            if event == QRCodeLoginEvents.DONE:
                status = 2
            elif event == QRCodeLoginEvents.SCAN:
                status = 0
            elif event == QRCodeLoginEvents.CONF:
                status = 1

            return status, credential if status == 2 else None
        except Exception as e:
            raise BusinessException(
                f"检查二维码状态失败: {str(e)}", ErrorCode.SYSTEM_ERROR)
