from qqmusic_api import Client
from qqmusic_api.models.login import QRLoginType, QR, QRLoginResult, QRCodeLoginEvents
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
import base64


class QQMusicService:
    @staticmethod
    async def get_qr_key(login_type: QRLoginType = QRLoginType.QQ) -> dict:
        try:
            async with Client() as client:
                qr = await client.login.get_qrcode(login_type)
                qr_base64 = base64.b64encode(qr.data).decode("utf-8")
                return {
                    "data": qr_base64,
                    "qr_type": qr.qr_type,
                    "mimetype": qr.mimetype,
                    "identifier": qr.identifier,
                }
        except Exception as e:
            raise BusinessException(f"获取二维码失败: {str(e)}", ErrorCode.SYSTEM_ERROR)

    @staticmethod
    async def check_qr_status(qr_data: dict) -> tuple[int, dict | None]:
        try:
            qr = QR(
                data=base64.b64decode(qr_data["data"]),
                qr_type=qr_data["qr_type"],
                mimetype=qr_data["mimetype"],
                identifier=qr_data["identifier"],
            )

            async with Client() as client:
                result: QRLoginResult = await client.login.check_qrcode(qr)
                status = -1

                if result.event == QRCodeLoginEvents.DONE:
                    status = 2
                elif result.event == QRCodeLoginEvents.SCAN:
                    status = 0
                elif result.event == QRCodeLoginEvents.CONF:
                    status = 1

                credential_dict = None
                if status == 2 and result.credential:
                    credential_dict = result.credential.model_dump()

                return status, credential_dict
        except Exception as e:
            raise BusinessException(
                f"检查二维码状态失败: {str(e)}", ErrorCode.SYSTEM_ERROR
            )
