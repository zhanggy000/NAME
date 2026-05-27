"""名人库导入工具。支持两种来源：
- seed：data/seed/famous_names_corpus.py 的精选 58 位
- wikidata：data/raw/wikidata_famous.jsonl（由 fetch_wikidata_famous.py 生成）
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from famous_names_corpus import FAMOUS_NAMES  # noqa: E402

DEFAULT_WIKIDATA_JSONL = ROOT / "data" / "raw" / "wikidata_famous.jsonl"

# 常见复姓（用于切分 surname/given_name）
COMPOUND_SURNAMES = {
    "欧阳", "司马", "诸葛", "上官", "司徒", "慕容", "皇甫", "长孙", "尉迟",
    "公孙", "东方", "西门", "南宫", "夏侯", "宇文", "完颜", "钟离", "司空",
    "万俟", "闻人", "赫连", "澹台", "公冶", "宗政", "濮阳", "淳于", "单于",
    "太叔", "申屠", "颛孙", "端木", "巫马", "段干", "百里", "东郭", "南门",
    "羊舌", "梁丘", "左丘", "东门", "西门", "微生", "梁丘", "拓跋", "独孤",
    "令狐", "纳兰", "爱新觉罗",
}

OCC_CATEGORY = [
    (("诗人", "诗"), "诗人"),
    (("作家", "小说家", "散文家", "文学家", "剧作家"), "文学家"),
    (("画家", "书法家", "艺术家", "雕塑家", "音乐家", "作曲家"), "艺术家"),
    (("演员", "歌手", "导演", "制片", "主持"), "演艺"),
    (("运动员", "球员"), "运动员"),
    (("科学家", "物理", "化学", "数学", "生物", "天文", "工程师"), "科学家"),
    (("哲学家", "思想家"), "思想家"),
    (("政治家", "外交家", "首相", "总理", "总统", "皇帝", "国君", "君主", "公"), "政治家"),
    (("军事家", "将领", "将军", "元帅", "军人"), "军事家"),
    (("历史学家", "考古学家", "学者", "教授"), "学者"),
    (("企业家", "商人", "实业家"), "企业家"),
    (("僧人", "高僧", "道士", "和尚"), "宗教人士"),
    (("医", "中医", "药"), "医学家"),
]

DYNASTY_RANGES = [
    (-2070, -1600, "夏"),
    (-1600, -1046, "商"),
    (-1046, -771, "西周"),
    (-770, -221, "先秦"),
    (-221, -206, "秦"),
    (-206, 220, "汉"),
    (220, 280, "三国"),
    (280, 420, "晋"),
    (420, 589, "南北朝"),
    (581, 618, "隋"),
    (618, 907, "唐"),
    (907, 960, "五代"),
    (960, 1279, "宋"),
    (1279, 1368, "元"),
    (1368, 1644, "明"),
    (1644, 1912, "清"),
    (1912, 1949, "民国"),
    (1949, 2100, "现代"),
]


CREATE_FAMOUS_TABLE = """
CREATE TABLE IF NOT EXISTS famous_names (
    name_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    surname TEXT,
    given_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    era TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    gender TEXT CHECK (gender IN ('男','女','未知')),
    brief TEXT,
    achievements TEXT,
    reference_url TEXT,
    fame_score INTEGER NOT NULL DEFAULT 50,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(full_name, era, category)
);
"""


CREATE_CHARACTER_FAMOUS_TABLE = """
CREATE TABLE IF NOT EXISTS character_famous (
    char TEXT NOT NULL,
    name_id INTEGER NOT NULL,
    position INTEGER,
    PRIMARY KEY (char, name_id),
    FOREIGN KEY (name_id) REFERENCES famous_names(name_id) ON DELETE CASCADE
);
"""


INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_famous_surname ON famous_names (surname)",
    "CREATE INDEX IF NOT EXISTS idx_famous_category ON famous_names (category)",
    "CREATE INDEX IF NOT EXISTS idx_famous_era ON famous_names (era)",
    "CREATE INDEX IF NOT EXISTS idx_famous_gender ON famous_names (gender)",
    "CREATE INDEX IF NOT EXISTS idx_famous_fame ON famous_names (fame_score DESC)",
    "CREATE INDEX IF NOT EXISTS idx_character_famous_char ON character_famous (char)",
    "CREATE INDEX IF NOT EXISTS idx_character_famous_name ON character_famous (name_id)",
]


UPSERT_FAMOUS = """
INSERT INTO famous_names (
    full_name, surname, given_name, category, era, birth_year, death_year,
    gender, brief, reference_url, fame_score, source
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(full_name, era, category) DO UPDATE SET
    surname = excluded.surname,
    given_name = excluded.given_name,
    gender = excluded.gender,
    brief = excluded.brief,
    birth_year = COALESCE(excluded.birth_year, famous_names.birth_year),
    death_year = COALESCE(excluded.death_year, famous_names.death_year),
    reference_url = excluded.reference_url,
    fame_score = MAX(famous_names.fame_score, excluded.fame_score),
    source = excluded.source
RETURNING name_id;
"""


# ============================================================
# 名字解析
# ============================================================

NAME_CLEAN_RE = re.compile(r"[（(].*?[)）]")  # 移除消歧义括号


def clean_full_name(raw: str) -> str:
    return NAME_CLEAN_RE.sub("", raw).strip()


def split_name(full_name: str) -> tuple[str, str]:
    """切分姓氏与名。返回 (surname, given_name)。"""
    if len(full_name) >= 3 and full_name[:2] in COMPOUND_SURNAMES:
        return full_name[:2], full_name[2:]
    if len(full_name) >= 2:
        return full_name[:1], full_name[1:]
    return "", full_name


def is_chinese(text: str) -> bool:
    return bool(text) and all("一" <= c <= "鿿" for c in text)


def map_gender(label: str | None) -> str:
    if not label:
        return "未知"
    if "女" in label or "female" in label.lower():
        return "女"
    if "男" in label or "male" in label.lower():
        return "男"
    return "未知"


def map_category(occ_label: str | None, brief: str | None) -> str | None:
    text = " ".join(filter(None, [occ_label, brief]))
    if not text:
        return None
    for keywords, cat in OCC_CATEGORY:
        if any(kw in text for kw in keywords):
            return cat
    return None


def parse_year(iso: str | None) -> int | None:
    """Wikidata 时间格式：'+1234-00-00T00:00:00Z' 或 '-0551-00-00T00:00:00Z'。"""
    if not iso:
        return None
    m = re.match(r"^([+-]?)(\d{1,5})-", iso)
    if not m:
        return None
    sign, year = m.group(1), int(m.group(2))
    return -year if sign == "-" else year


def year_to_era(year: int | None) -> str | None:
    if year is None:
        return None
    for start, end, era in DYNASTY_RANGES:
        if start <= year < end:
            return era
    return None


def fame_from_sitelinks(sitelinks: int) -> int:
    """sitelinks 转 fame_score。8→50, 30→70, 100→90, 200+→95+"""
    if sitelinks >= 200:
        return min(100, 90 + (sitelinks - 200) // 50)
    if sitelinks >= 100:
        return 85 + (sitelinks - 100) // 10
    if sitelinks >= 50:
        return 70 + (sitelinks - 50) * 3 // 10
    if sitelinks >= 20:
        return 55 + (sitelinks - 20) // 2
    return 40 + (sitelinks - 8)


# ============================================================
# 入库
# ============================================================

def init_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_FAMOUS_TABLE)
    conn.execute(CREATE_CHARACTER_FAMOUS_TABLE)
    for sql in INDEXES:
        conn.execute(sql)
    conn.commit()


def upsert_one(conn: sqlite3.Connection, record: dict, source: str) -> int | None:
    row = conn.execute(
        UPSERT_FAMOUS,
        (
            record["full_name"],
            record["surname"],
            record["given_name"],
            record.get("category"),
            record.get("era"),
            record.get("birth_year"),
            record.get("death_year"),
            record.get("gender", "未知"),
            record.get("brief"),
            record.get("reference_url"),
            record.get("fame_score", 50),
            source,
        ),
    ).fetchone()
    if not row:
        return None
    name_id = row[0]
    conn.execute("DELETE FROM character_famous WHERE name_id = ?", (name_id,))
    given = record["given_name"]
    conn.executemany(
        "INSERT OR REPLACE INTO character_famous (char, name_id, position) VALUES (?, ?, ?)",
        [(c, name_id, idx) for idx, c in enumerate(given) if is_chinese(c)],
    )
    return name_id


def import_seed(conn: sqlite3.Connection) -> int:
    count = 0
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for full_name, surname, given_name, category, era, gender, brief, fame_score in FAMOUS_NAMES:
            rec = {
                "full_name": full_name,
                "surname": surname,
                "given_name": given_name,
                "category": category,
                "era": era,
                "gender": gender,
                "brief": brief,
                "fame_score": fame_score,
            }
            if upsert_one(conn, rec, source="famous_seed") is not None:
                count += 1
    return count


def import_wikidata(conn: sqlite3.Connection, jsonl_path: Path) -> tuple[int, int]:
    imported = 0
    skipped = 0
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                full_name = clean_full_name(raw.get("label_zh", ""))
                if not is_chinese(full_name) or len(full_name) < 2 or len(full_name) > 6:
                    skipped += 1
                    continue
                surname, given_name = split_name(full_name)
                if not given_name:
                    skipped += 1
                    continue
                birth_year = parse_year(raw.get("birth"))
                death_year = parse_year(raw.get("death"))
                era_year = birth_year if birth_year is not None else death_year
                rec = {
                    "full_name": full_name,
                    "surname": surname,
                    "given_name": given_name,
                    "category": map_category(raw.get("occupation_label"), raw.get("description_zh")),
                    "era": year_to_era(era_year),
                    "birth_year": birth_year,
                    "death_year": death_year,
                    "gender": map_gender(raw.get("gender_label")),
                    "brief": raw.get("description_zh") or raw.get("occupation_label"),
                    "reference_url": f"https://www.wikidata.org/wiki/{raw['qid']}",
                    "fame_score": fame_from_sitelinks(int(raw["sitelinks"])),
                }
                if upsert_one(conn, rec, source="wikidata") is not None:
                    imported += 1
                else:
                    skipped += 1
    return imported, skipped


def refresh_char_famous_count(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "characters"):
        return
    if not _column_exists(conn, "characters", "famous_count"):
        return
    with conn:
        conn.execute("UPDATE characters SET famous_count = 0")
        conn.execute(
            """
            UPDATE characters
            SET famous_count = (
                SELECT COUNT(*) FROM character_famous
                WHERE character_famous.char = characters.char
            )
            WHERE char IN (SELECT DISTINCT char FROM character_famous)
            """
        )


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


def _column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    return any(row[1] == column_name for row in conn.execute(f"PRAGMA table_info({table_name})"))


def main() -> None:
    parser = argparse.ArgumentParser(description="导入名人库并建立单字反向索引")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--source", choices=["seed", "wikidata", "all"], default="seed")
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_WIKIDATA_JSONL)
    args = parser.parse_args()

    with sqlite3.connect(args.sqlite) as conn:
        init_sqlite(conn)
        total = 0
        if args.source in ("seed", "all"):
            n = import_seed(conn)
            total += n
            print(f"[seed] 导入 {n} 位")
        if args.source in ("wikidata", "all"):
            if not args.jsonl.exists():
                sys.exit(f"找不到 JSONL：{args.jsonl}，请先跑 scripts/fetch_wikidata_famous.py")
            n, skipped = import_wikidata(conn, args.jsonl)
            total += n
            print(f"[wikidata] 导入 {n} 位，跳过 {skipped} 位")
        refresh_char_famous_count(conn)
    print(f"已写入 {total} 位 → {args.sqlite}")


if __name__ == "__main__":
    main()
