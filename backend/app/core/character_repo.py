"""
单字数据访问层。

优先级：SQLite (data/name.db) > 内存种子 (characters_seed.py)。

提供与原 characters_seed.get_char / find_chars 完全兼容的接口，
但额外携带 classics_count / famous_count，方便评分层使用反查结果。

数据库不存在或表不全时自动回退到种子，让单元测试/裸 clone 仓库也能跑。
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "data" / "seed"))

from characters_seed import (  # noqa: E402
    CHARACTERS_SEED,
    get_char as _seed_get_char,
    find_chars as _seed_find_chars,
)


# data/name.db 的位置可被环境变量覆盖（测试用）
_DB_PATH_ENV = "NAME_DB_PATH"
_DEFAULT_DB_PATH = _ROOT / "data" / "name.db"

_lock = threading.Lock()
_cache_by_char: dict[str, dict] | None = None  # 全表缓存（启动时一次性读完）
_cache_loaded: bool = False  # 是否已尝试过加载（None 值也算"加载完毕，结果为空"）


def _db_path() -> Path:
    env = os.environ.get(_DB_PATH_ENV)
    return Path(env) if env else _DEFAULT_DB_PATH


def _table_has_rows(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='characters'"
    ).fetchone()
    if not row:
        return False
    return conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0] > 0


def _row_to_dict(row: sqlite3.Row) -> dict:
    """SQLite 行 → seed 风格 dict（保持下游代码不需要改）。"""
    def _parse_json(value, default):
        if not value:
            return default
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default

    return {
        "char": row["char"],
        "pinyin": row["pinyin"],
        "tone": row["tone"],
        "kangxi": row["kangxi_strokes"],
        "simplified": row["simplified_strokes"],
        "wuxing": row["wuxing"],
        "wuxing_source": row["wuxing_source"],
        "wuxing_confidence": row["wuxing_confidence"],
        "radical": row["radical"],
        "meaning": row["meaning_primary"],
        "gender_pref": row["gender_pref"],
        "style_tags": _parse_json(row["style_tags"], []),
        "classics_refs": _parse_json(row["classics_refs"], []),
        "famous_refs": _parse_json(row["famous_refs"], []),
        "classics_count": row["classics_count"] if "classics_count" in row.keys() else 0,
        "famous_count": row["famous_count"] if "famous_count" in row.keys() else 0,
        "is_common": bool(row["is_common"]),
        "is_rare": bool(row["is_rare"]),
        "is_taboo": bool(row["is_taboo"]),
        "data_source": row["data_source"],
    }


def _load_from_db() -> dict[str, dict] | None:
    db_path = _db_path()
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_has_rows(conn):
                return None
            rows = conn.execute("SELECT * FROM characters").fetchall()
    except sqlite3.Error:
        return None
    return {row["char"]: _row_to_dict(row) for row in rows}


def _ensure_cache() -> dict[str, dict] | None:
    """惰性加载缓存。首次调用时读 DB，之后直接返回内存对象。

    生成阶段每次请求会调用 get_char/find_chars 数千次，因此不在热路径上
    做 stat()/锁/重新加载；如果导入了新数据，请显式调用 invalidate_cache()
    或重启进程。
    """
    global _cache_by_char, _cache_loaded
    if _cache_loaded:
        return _cache_by_char
    with _lock:
        if _cache_loaded:
            return _cache_by_char
        _cache_by_char = _load_from_db()
        _cache_loaded = True
        return _cache_by_char


def invalidate_cache() -> None:
    """测试或导入完数据后强制刷新。"""
    global _cache_by_char, _cache_loaded
    with _lock:
        _cache_by_char = None
        _cache_loaded = False


# ============================================================
# 公共 API（保持与 characters_seed 同名同签名）
# ============================================================

def get_char(ch: str) -> Optional[dict]:
    cache = _ensure_cache()
    if cache and ch in cache:
        return cache[ch]
    return _seed_get_char(ch)


def find_chars(
    wuxing: str | None = None,
    kangxi: int | None = None,
    gender: str | None = None,
    style_tags: list[str] | None = None,
) -> list[dict]:
    """按条件筛选字。多条件 AND。SQLite 可用时从库里筛，否则回退种子。"""
    cache = _ensure_cache()
    if cache:
        pool = cache.values()
        result = []
        for entry in pool:
            if wuxing and entry["wuxing"] != wuxing:
                continue
            if kangxi is not None and entry["kangxi"] != kangxi:
                continue
            if gender and entry["gender_pref"] not in (gender, "中性"):
                continue
            if style_tags and not any(t in entry.get("style_tags", []) for t in style_tags):
                continue
            # 取名时排除明显未校对的"待校对"字（避免 Unihan 兜底字进生成池）
            if "待校对" in entry.get("style_tags", []):
                continue
            result.append(entry)
        return result

    return _seed_find_chars(
        wuxing=wuxing, kangxi=kangxi, gender=gender, style_tags=style_tags
    )


def repo_stats() -> dict:
    """供 trace/调试用，告诉调用方当前是哪个来源、有多少条记录。"""
    cache = _ensure_cache()
    if cache:
        return {
            "source": "sqlite",
            "db_path": str(_db_path()),
            "total": len(cache),
            "naming_ready": sum(
                1 for c in cache.values()
                if c.get("style_tags") and "待校对" not in c.get("style_tags", [])
            ),
        }
    return {
        "source": "seed",
        "db_path": None,
        "total": len(CHARACTERS_SEED),
        "naming_ready": sum(1 for c in CHARACTERS_SEED if c.get("style_tags")),
    }
