from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.common.exceptions.business_exception import BusinessException
from app.common.constants.error_code import ErrorCode
from app.utils.helpers import ResponseUtil

async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content=ResponseUtil.error(exc.message, exc.code, exc.data)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=200,
        content=ResponseUtil.error(str(exc), ErrorCode.PARAM_ERROR)
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=200,
        content=ResponseUtil.error(exc.detail, exc.status_code)
    )

def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler) 