from typing import Any, Dict
from datetime import datetime
from app.common.constants.error_code import ErrorCode

class ResponseUtil:
    @staticmethod
    def success(data: Any, message: str = "Success") -> Dict[str, Any]:
        return {
            "code": ErrorCode.SYSTEM_OK,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def error(message: str, code: int = ErrorCode.SYSTEM_ERROR, data: Any = None) -> Dict[str, Any]:
        return {
            "code": code,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        } 