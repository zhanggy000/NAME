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
import zipfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from character_reviews import REVIEWED_CHARACTERS  # noqa: E402
from characters_seed import CHARACTERS_SEED  # noqa: E402

PINYIN_TONE_MARKS = {
    "ā": ("a", 1), "á": ("a", 2), "ǎ": ("a", 3), "à": ("a", 4),
    "ē": ("e", 1), "é": ("e", 2), "ě": ("e", 3), "è": ("e", 4),
    "ī": ("i", 1), "í": ("i", 2), "ǐ": ("i", 3), "ì": ("i", 4),
    "ō": ("o", 1), "ó": ("o", 2), "ǒ": ("o", 3), "ò": ("o", 4),
    "ū": ("u", 1), "ú": ("u", 2), "ǔ": ("u", 3), "ù": ("u", 4),
    "ǖ": ("ü", 1), "ǘ": ("ü", 2), "ǚ": ("ü", 3), "ǜ": ("ü", 4),
    "ń": ("n", 2), "ň": ("n", 3), "ǹ": ("n", 4),
    "ḿ": ("m", 2),
}

RADICAL_WUXING = {
    # 木
    "75": ("木", "radical_木", 70),
    "118": ("木", "radical_竹", 65),
    "140": ("木", "radical_艸", 65),
    # 火
    "72": ("火", "radical_日", 70),
    "86": ("火", "radical_火", 75),
    # 土
    "32": ("土", "radical_土", 75),
    "46": ("土", "radical_山", 65),
    "170": ("土", "radical_阜", 60),
    # 金
    "18": ("金", "radical_刀", 60),
    "167": ("金", "radical_金", 75),
    # 水
    "85": ("水", "radical_水", 75),
    "173": ("水", "radical_雨", 70),
}


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

    reviewed = REVIEWED_CHARACTERS.get(raw["char"], {})
    wuxing_source = reviewed.get("wuxing_source") or raw.get("wuxing_source") or "seed_manual"
    wuxing_confidence = reviewed.get(
        "wuxing_confidence",
        raw.get("wuxing_confidence", 85 if not is_surname else 75),
    )

    return {
        "char": raw["char"],
        "pinyin": raw["pinyin"],
        "tone": int(raw["tone"]),
        "kangxi_strokes": int(raw["kangxi"]),
        "simplified_strokes": int(raw["simplified"]),
        "wuxing": reviewed.get("wuxing", raw["wuxing"]),
        "wuxing_source": wuxing_source,
        "wuxing_confidence": int(wuxing_confidence),
        "radical": raw.get("radical"),
        "meaning_primary": reviewed.get("meaning", raw["meaning"]),
        "gender_pref": reviewed.get("gender_pref", raw.get("gender_pref", "中性")),
        "style_tags": json.dumps(reviewed.get("style_tags", style_tags), ensure_ascii=False),
        "classics_refs": json.dumps(
            reviewed.get("classics_refs", raw.get("classics_refs") or []),
            ensure_ascii=False,
        ),
        "famous_refs": json.dumps(
            reviewed.get("famous_refs", raw.get("famous_refs") or []),
            ensure_ascii=False,
        ),
        "is_common": 1,
        "is_rare": int(raw.get("is_rare", False)),
        "is_taboo": int(raw.get("is_taboo", False)),
        "data_source": data_source,
    }


def parse_marked_pinyin(value: str) -> tuple[str, int]:
    """从带调拼音中提取原文拼音和声调。"""
    first = value.split()[0]
    tone = 5
    for char in first:
        if char in PINYIN_TONE_MARKS:
            tone = PINYIN_TONE_MARKS[char][1]
            break
    return first, tone


def parse_unihan_zip(zip_path: Path, limit: int = 5000) -> list[dict]:
    """解析 Unihan zip，返回 IICore 中的基础常用汉字记录。"""
    strokes: dict[str, int] = {}
    radicals: dict[str, str] = {}
    mandarin: dict[str, str] = {}
    iicore: set[str] = set()

    with zipfile.ZipFile(zip_path) as zf:
        for raw in zf.open("Unihan_IRGSources.txt"):
            line = raw.decode("utf-8").strip()
            if not line or line.startswith("#"):
                continue
            code, field, value = line.split("\t", 2)
            if field == "kTotalStrokes":
                strokes[code] = int(value.split()[0])
            elif field == "kRSUnicode":
                radicals[code] = value.split(".")[0].strip("'")
            elif field == "kIICore":
                iicore.add(code)

        for raw in zf.open("Unihan_Readings.txt"):
            line = raw.decode("utf-8").strip()
            if not line or line.startswith("#"):
                continue
            code, field, value = line.split("\t", 2)
            if field == "kMandarin":
                mandarin[code] = value

    rows = []
    for code in sorted(iicore, key=lambda item: int(item[2:], 16)):
        codepoint = int(code[2:], 16)
        if not 0x4E00 <= codepoint <= 0x9FFF:
            continue
        if code not in strokes or code not in mandarin:
            continue

        radical_no = radicals.get(code, "")
        wuxing, source, confidence = RADICAL_WUXING.get(
            radical_no, ("土", "unihan_iicore_default", 35)
        )
        pinyin, tone = parse_marked_pinyin(mandarin[code])
        char = chr(codepoint)
        rows.append({
            "char": char,
            "pinyin": pinyin,
            "tone": tone,
            "kangxi": strokes[code],
            "simplified": strokes[code],
            "wuxing": wuxing,
            "wuxing_source": source,
            "wuxing_confidence": confidence,
            "radical": radical_no or None,
            "meaning": "Unihan IICore 常用汉字，取名释义待人工校对",
            "gender_pref": "中性",
            "style_tags": ["待校对"],
        })
        if len(rows) >= limit:
            break

    return rows


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


def import_unihan(db_path: Path, zip_path: Path, limit: int) -> int:
    rows = parse_unihan_zip(zip_path, limit=limit)
    if len(rows) < limit:
        raise ValueError(f"Unihan 可导入记录不足：需要 {limit}，实际 {len(rows)}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        init_sqlite(conn)
        count = import_characters(conn, rows, data_source="unihan_iicore")
        count += import_characters(conn, CHARACTERS_SEED, data_source="characters_seed")
        return count


def main() -> None:
    parser = argparse.ArgumentParser(description="导入单字库数据")
    parser.add_argument(
        "--source",
        choices=["seed", "unihan"],
        default="seed",
        help="导入来源，默认 seed",
    )
    parser.add_argument(
        "--sqlite",
        type=Path,
        default=ROOT / "data" / "name.db",
        help="SQLite 数据库路径，默认 data/name.db",
    )
    parser.add_argument(
        "--unihan-zip",
        type=Path,
        default=ROOT / "data" / "raw" / "Unihan.zip",
        help="Unihan.zip 路径，source=unihan 时使用",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="source=unihan 时导入的记录数，默认 5000",
    )
    args = parser.parse_args()

    if args.source == "seed":
        count = import_seed(args.sqlite)
    else:
        count = import_unihan(args.sqlite, args.unihan_zip, args.limit)
    print(f"已导入/更新 {count} 个单字 → {args.sqlite}")


if __name__ == "__main__":
    main()
