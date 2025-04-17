import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.middleware import ExtractMiddleware
from app.core.exceptions import setup_exception_handlers

# logging.basicConfig(
#     format="%(levelname)s [%(asctime)s] %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
#     level=logging.DEBUG,
# )

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加自定义中间件
app.add_middleware(ExtractMiddleware)  # 先处理请求参数

# 设置异常处理器
setup_exception_handlers(app)

# 注册路由
app.include_router(api_router, prefix="")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app='main:app', host="0.0.0.0",
                port=8000)
