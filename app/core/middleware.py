import json
from fastapi import Request
from qqmusic_api import Credential
from starlette.middleware.base import BaseHTTPMiddleware
import time

class ExtractMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳过静态文件的处理
        if request.url.path.startswith("/static/"):
            return await call_next(request)
            
        # 添加基础参数
        request.state.base_params = {
            "timestamp": int(time.time() * 1000)
        }
        
        # 处理token
        token = request.headers.get("token") or request.headers.get("Token")
        if token:
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")
            token = json.loads(token)
            credential = Credential.from_cookies_dict(token)
            if await credential.is_expired():
                # 刷新token
                await credential.refresh()
            request.state.base_params["cookie"] = credential
        else:
            request.state.base_params["cookie"] = ""
            
        return await call_next(request)