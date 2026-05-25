"""请求日志 + 错误处理中间件"""
from __future__ import annotations

import time
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logging_config import setup_logging

logger = setup_logging()


async def request_logging_middleware(request: Request, call_next):
    """打印每个请求的耗时与状态"""
    start = time.time()
    try:
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({elapsed:.0f}ms)"
        )
        return response
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        logger.error(
            f"{request.method} {request.url.path} → 500 ({elapsed:.0f}ms): {e}"
        )
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(e),
                "path": request.url.path,
            }
        )
