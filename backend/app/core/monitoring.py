"""错误监控初始化。"""
from __future__ import annotations

from app.config import settings


def setup_monitoring() -> bool:
    if not settings.sentry_dsn:
        return False

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
    return True
