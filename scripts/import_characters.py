"""
单字库导入工具。

首版支持把 data/seed/characters_seed.py 导入 SQLite，作为批量数据源接入前的
可测试导入管线。后续扩展外部 JSON/CSV 或 PostgreSQL 时，应复用 normalize_character。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from characters_seed import CHARACTERS_SEED  # noqa: E402


CREATE_CHARACTERS_TABLE = """
CREATE TABLE IF NOT EXISTS characters (
    char TEXT PRIMARY KEY,
    pinyin TEXT NOT NULL,
    tone INTEGER NOT NULL CHECK (tone BETWEEN 1 AND 5),
    kangxi_strokes INTEGER NOT NULL,
    simplified_strokes INTEGER NOT NULL,
    wuxing TEXT NOT NULL CHECK (wuxing IN ('木','火','土','金','水')),
    wuxing_source TEXT,
    wuxing_confidence INTEGER NOT NULL DEFAULT 80,
    radical TEXT,
    meaning_primary TEXT NOT NULL,
    gender_pref TEXT NOT NULL DEFAULT '中性',
    style_tags TEXT NOT NULL DEFAULT '[]',
    classics_refs TEXT NOT NULL DEFAULT '[]',
    famous_refs TEXT NOT NULL DEFAULT '[]',
    is_common INTEGER NOT NULL DEFAULT 1,
    is_rare INTEGER NOT NULL DEFAULT 0,
    is_taboo INTEGER NOT NULL DEFAULT 0,
    data_source TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_characters_kangxi ON characters (kangxi_strokes)",
    "CREATE INDEX IF NOT EXISTS idx_characters_wuxing ON characters (wuxing)",
    "CREATE INDEX IF NOT EXISTS idx_characters_gender ON characters (gender_pref)",
    "CREATE INDEX IF NOT EXISTS idx_characters_common ON characters (is_common, is_rare)",
]


UPSERT_CHARACTER = """
INSERT INTO characters (
    char, pinyin, tone, kangxi_strokes, simplified_strokes, wuxing,
    wuxing_source, wuxing_confidence, radical, meaning_primary, gender_pref,
    style_tags, classics_refs, famous_refs, is_common, is_rare, is_taboo, data_source
) VALUES (
    :char, :pinyin, :tone, :kangxi_strokes, :simplified_strokes, :wuxing,
    :wuxing_source, :wuxing_confidence, :radical, :meaning_primary, :gender_pref,
    :style_tags, :classics_refs, :famous_refs, :is_common, :is_rare, :is_taboo, :data_source
)
ON CONFLICT(char) DO UPDATE SET
    pinyin = excluded.pinyin,
    tone = excluded.tone,
    kangxi_strokes = excluded.kangxi_strokes,
    simplified_strokes = excluded.simplified_strokes,
    wuxing = excluded.wuxing,
    wuxing_source = excluded.wuxing_source,
    wuxing_confidence = excluded.wuxing_confidence,
    radical = excluded.radical,
    meaning_primary = excluded.meaning_primary,
    gender_pref = excluded.gender_pref,
    style_tags = excluded.style_tags,
    classics_refs = excluded.classics_refs,
    famous_refs = excluded.famous_refs,
    is_common = excluded.is_common,
    is_rare = excluded.is_rare,
    is_taboo = excluded.is_taboo,
    data_source = excluded.data_source,
    updated_at = CURRENT_TIMESTAMP;
"""


def normalize_character(raw: dict, data_source: str = "characters_seed") -> dict:
    """把当前 seed 字段归一化为 characters 表字段。"""
    required = ["char", "pinyin", "tone", "kangxi", "simplified", "wuxing", "meaning"]
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError(f"字条目缺少字段 {missing}: {raw!r}")

    style_tags = raw.get("style_tags") or []
    is_surname = not style_tags and str(raw["meaning"]).startswith("姓氏")

    return {
        "char": raw["char"],
        "pinyin": raw["pinyin"],
        "tone": int(raw["tone"]),
        "kangxi_strokes": int(raw["kangxi"]),
        "simplified_strokes": int(raw["simplified"]),
        "wuxing": raw["wuxing"],
        "wuxing_source": raw.get("wuxing_source") or "seed_manual",
        "wuxing_confidence": int(raw.get("wuxing_confidence", 85 if not is_surname else 75)),
        "radical": raw.get("radical"),
        "meaning_primary": raw["meaning"],
        "gender_pref": raw.get("gender_pref", "中性"),
        "style_tags": json.dumps(style_tags, ensure_ascii=False),
        "classics_refs": json.dumps(raw.get("classics_refs") or [], ensure_ascii=False),
        "famous_refs": json.dumps(raw.get("famous_refs") or [], ensure_ascii=False),
        "is_common": 1,
        "is_rare": int(raw.get("is_rare", False)),
        "is_taboo": int(raw.get("is_taboo", False)),
        "data_source": data_source,
    }


def init_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_CHARACTERS_TABLE)
    for sql in CREATE_INDEXES:
        conn.execute(sql)
    conn.commit()


def import_characters(conn: sqlite3.Connection, rows: Iterable[dict], data_source: str) -> int:
    normalized = [normalize_character(row, data_source=data_source) for row in rows]
    with conn:
        conn.executemany(UPSERT_CHARACTER, normalized)
    return len(normalized)


def import_seed(db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        init_sqlite(conn)
        return import_characters(conn, CHARACTERS_SEED, data_source="characters_seed")


def main() -> None:
    parser = argparse.ArgumentParser(description="导入单字库数据")
    parser.add_argument(
        "--sqlite",
        type=Path,
        default=ROOT / "data" / "name.db",
        help="SQLite 数据库路径，默认 data/name.db",
    )
    args = parser.parse_args()

    count = import_seed(args.sqlite)
    print(f"已导入/更新 {count} 个单字 → {args.sqlite}")


if __name__ == "__main__":
    main()
