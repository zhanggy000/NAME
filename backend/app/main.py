"""FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.api.routes import router as api_router
from app.api.middleware import request_logging_middleware
from app.core.logging_config import setup_logging


logger = setup_logging(level=settings.log_level, log_file=settings.log_file)


app = FastAPI(
    title="NAME · 智能取名系统",
    description="综合八字命理 + 文化典籍 + AI 复审的取名工具",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册请求日志中间件
app.middleware("http")(request_logging_middleware)

app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"NAME v{__version__} 启动 · env={settings.app_env}")


@app.get("/")
def root():
    return {
        "name": "NAME",
        "version": __version__,
        "env": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
