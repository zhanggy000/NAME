"""日志配置 · 基于 loguru"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("name")


def setup_logging(level: str = "INFO", log_file: str | None = None):
    """配置全局 logger"""
    if hasattr(logger, "remove"):
        # loguru API
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                   "<cyan>{name}:{line}</cyan> | {message}",
            level=level,
        )
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                log_file,
                rotation="10 MB",
                retention="14 days",
                level=level,
                encoding="utf-8",
            )
    return logger
