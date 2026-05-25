"""FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.api.routes import router as api_router


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

app.include_router(api_router)


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
