"""
字→典籍 / 字→名人 反查的数据访问层。

优先 SQLite (character_classics / character_famous JOIN)，
不可用时回退到 data/seed 里的 92 条精选典籍 + 58 位精选名人。

返回结构与 seed 版函数保持一致，下游 scoring.py 无需感知差异。
"""
from __future__ import annotations

import sqlite3
import sys
import threading
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "data" / "seed"))

from classics_corpus import get_classics_for_char as _seed_classics  # noqa: E402
from famous_names_corpus import get_famous_for_char as _seed_famous  # noqa: E402

from app.core.character_repo import _db_path  # noqa: E402


_lock = threading.Lock()
_db_available: bool | None = None  # 缓存"DB 是否可用"，避免每次 stat


def _check_db_available() -> bool:
    global _db_available
    if _db_available is not None:
        return _db_available
    with _lock:
        if _db_available is not None:
            return _db_available
        path = _db_path()
        if not path.exists():
            _db_available = False
            return False
        try:
            with sqlite3.connect(str(path)) as conn:
                has_classics = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='character_classics'"
                ).fetchone() is not None
                has_famous = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='character_famous'"
                ).fetchone() is not None
            _db_available = has_classics or has_famous
        except sqlite3.Error:
            _db_available = False
        return _db_available


def invalidate_cache() -> None:
    global _db_available
    with _lock:
        _db_available = None
    get_classics_for_char.cache_clear()
    _famous_cached.cache_clear()


# ============================================================
# 典籍反查
# ============================================================

CLASSICS_QUERY = """
SELECT c.book, c.chapter, c.line_text, c.era, c.author
FROM character_classics cc
JOIN classics c ON c.ref_id = cc.ref_id
WHERE cc.char = ?
ORDER BY
    CASE c.book
        WHEN '诗经' THEN 1 WHEN '楚辞' THEN 2 WHEN '论语' THEN 3
        WHEN '周易' THEN 4 WHEN '道德经' THEN 5 ELSE 9
    END,
    c.ref_id
"""


@lru_cache(maxsize=8192)
def get_classics_for_char(ch: str) -> list[dict]:
    """查含某字的典籍引用。结构同 seed 版：{book, chapter, line, era, author}

    LRU 缓存避免在批量生成时反复打开 SQLite 连接（典型一次生成会被同一个字
    查询数百次）。
    """
    if not _check_db_available():
        return _seed_classics(ch)
    try:
        with sqlite3.connect(str(_db_path())) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(CLASSICS_QUERY, (ch,)).fetchall()
    except sqlite3.Error:
        return _seed_classics(ch)

    if not rows:
        return _seed_classics(ch)

    return [
        {
            "book": r["book"],
            "chapter": r["chapter"],
            "line": r["line_text"],
            "era": r["era"],
            "author": r["author"],
        }
        for r in rows
    ]


# ============================================================
# 名人反查
# ============================================================

FAMOUS_QUERY = """
SELECT full_name, surname, given_name, category, era, gender,
       brief, fame_score, source
FROM famous_names f
JOIN character_famous cf ON cf.name_id = f.name_id
WHERE cf.char = ?
ORDER BY f.fame_score DESC, f.name_id
LIMIT ?
"""


@lru_cache(maxsize=8192)
def _famous_cached(ch: str, limit: int) -> tuple:
    """LRU 缓存内部实现；返回元组以保证可哈希；外层再转回 list[dict]。"""
    if not _check_db_available():
        return tuple(tuple(sorted(d.items())) for d in _seed_famous(ch, limit=limit))
    try:
        with sqlite3.connect(str(_db_path())) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(FAMOUS_QUERY, (ch, limit)).fetchall()
    except sqlite3.Error:
        return tuple(tuple(sorted(d.items())) for d in _seed_famous(ch, limit=limit))

    if not rows:
        return tuple(tuple(sorted(d.items())) for d in _seed_famous(ch, limit=limit))

    return tuple(tuple(sorted(dict(r).items())) for r in rows)


def get_famous_for_char(ch: str, limit: int = 10) -> list[dict]:
    """查用过某字的名人，按知名度倒序。结构同 seed 版。"""
    return [dict(items) for items in _famous_cached(ch, limit)]
