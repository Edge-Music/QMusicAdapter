from app.common.constants.error_code import ErrorCode

class BusinessException(Exception):
    def __init__(self, message: str, code: int = ErrorCode.SYSTEM_ERROR, data: any = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message) 