import json
from fastapi import Request
from qqmusic_api import Credential, Client
from starlette.middleware.base import BaseHTTPMiddleware
import time


class ExtractMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/static/"):
            return await call_next(request)

        request.state.base_params = {"timestamp": int(time.time() * 1000)}

        token = request.headers.get("token") or request.headers.get("Token")
        if token:
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")
            token_dict = json.loads(token)
            credential = Credential.model_validate(token_dict)
            if credential.is_expired():
                try:
                    async with Client() as client:
                        await credential.refresh(client)
                        token_dict = credential.model_dump()
                except Exception:
                    pass
            request.state.base_params["cookie"] = token_dict
        else:
            request.state.base_params["cookie"] = None

        return await call_next(request)
