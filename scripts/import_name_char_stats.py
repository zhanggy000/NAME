"""Build given-name character statistics from real-name corpora.

This is an evidence layer, not a final naming dictionary. It records which
characters are actually used in given names, then later review steps can decide
which characters are safe and tasteful enough for generation.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from famous_names_corpus import FAMOUS_NAMES  # noqa: E402

DEFAULT_WIKIDATA_JSONL = ROOT / "data" / "raw" / "wikidata_famous.jsonl"
DEFAULT_CHINAPIS_CSV = ROOT / "data" / "raw" / "chinapis_given_name_df.csv"

COMPOUND_CHINESE_SURNAMES = {
    "欧阳", "司马", "诸葛", "上官", "司徒", "慕容", "皇甫", "长孙", "尉迟",
    "公孙", "东方", "西门", "南宫", "夏侯", "宇文", "完颜", "钟离", "司空",
    "万俟", "闻人", "赫连", "澹台", "公冶", "宗政", "濮阳", "淳于", "单于",
    "太叔", "申屠", "颛孙", "端木", "巫马", "段干", "百里", "东郭", "南门",
    "羊舌", "梁丘", "左丘", "东门", "微生", "拓跋", "独孤", "令狐", "纳兰",
    "爱新觉罗",
}

COMMON_CHINESE_SURNAMES = set(
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    "戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐"
    "费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平"
    "黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋庞熊纪舒屈项祝董"
    "梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田胡凌"
    "霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉龚"
    "程嵇邢裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓"
    "牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘斜厉戎祖武符刘景詹束"
    "龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍"
    "双闻莘党翟谭贡劳逄姬申扶堵冉雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农"
    "温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满"
    "弘匡国文寇广禄阙东殴殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简"
    "饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公"
)


def clean_full_name(raw: str) -> str:
    return raw.split("（", 1)[0].split("(", 1)[0].strip()


def is_chinese(text: str) -> bool:
    return bool(text) and all("一" <= char <= "鿿" for char in text)


def map_gender(label: str | None) -> str:
    if not label:
        return "未知"
    lower = label.lower()
    if "女" in label or "female" in lower:
        return "女"
    if "男" in label or "male" in lower:
        return "男"
    return "未知"


def fame_from_sitelinks(sitelinks: int) -> int:
    if sitelinks >= 200:
        return min(100, 90 + (sitelinks - 200) // 50)
    if sitelinks >= 100:
        return 85 + (sitelinks - 100) // 10
    if sitelinks >= 50:
        return 70 + (sitelinks - 50) * 3 // 10
    if sitelinks >= 20:
        return 55 + (sitelinks - 20) // 2
    return 40 + (sitelinks - 8)

CREATE_NAME_CHAR_STATS = """
CREATE TABLE IF NOT EXISTS name_char_stats (
    char TEXT PRIMARY KEY,
    total_count INTEGER NOT NULL DEFAULT 0,
    distinct_name_count INTEGER NOT NULL DEFAULT 0,
    male_count INTEGER NOT NULL DEFAULT 0,
    female_count INTEGER NOT NULL DEFAULT 0,
    unknown_gender_count INTEGER NOT NULL DEFAULT 0,
    position_1_count INTEGER NOT NULL DEFAULT 0,
    position_2_count INTEGER NOT NULL DEFAULT 0,
    position_other_count INTEGER NOT NULL DEFAULT 0,
    weighted_fame INTEGER NOT NULL DEFAULT 0,
    source_count INTEGER NOT NULL DEFAULT 0,
    sources TEXT NOT NULL DEFAULT '[]',
    sample_names TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_name_char_stats_total ON name_char_stats (total_count DESC)",
    (
        "CREATE INDEX IF NOT EXISTS idx_name_char_stats_distinct "
        "ON name_char_stats (distinct_name_count DESC)"
    ),
    "CREATE INDEX IF NOT EXISTS idx_name_char_stats_fame ON name_char_stats (weighted_fame DESC)",
]

UPSERT_STAT = """
INSERT INTO name_char_stats (
    char, total_count, distinct_name_count, male_count, female_count,
    unknown_gender_count, position_1_count, position_2_count, position_other_count,
    weighted_fame, source_count, sources, sample_names
) VALUES (
    :char, :total_count, :distinct_name_count, :male_count, :female_count,
    :unknown_gender_count, :position_1_count, :position_2_count, :position_other_count,
    :weighted_fame, :source_count, :sources, :sample_names
)
ON CONFLICT(char) DO UPDATE SET
    total_count = excluded.total_count,
    distinct_name_count = excluded.distinct_name_count,
    male_count = excluded.male_count,
    female_count = excluded.female_count,
    unknown_gender_count = excluded.unknown_gender_count,
    position_1_count = excluded.position_1_count,
    position_2_count = excluded.position_2_count,
    position_other_count = excluded.position_other_count,
    weighted_fame = excluded.weighted_fame,
    source_count = excluded.source_count,
    sources = excluded.sources,
    sample_names = excluded.sample_names,
    updated_at = CURRENT_TIMESTAMP;
"""


@dataclass(frozen=True)
class NameRecord:
    full_name: str
    given_name: str
    gender: str
    fame_score: int
    source: str


@dataclass
class CharStat:
    char: str
    total_count: int = 0
    names: set[str] = field(default_factory=set)
    male_count: int = 0
    female_count: int = 0
    unknown_gender_count: int = 0
    position_1_count: int = 0
    position_2_count: int = 0
    position_other_count: int = 0
    weighted_fame: int = 0
    sources: set[str] = field(default_factory=set)
    sample_names: list[str] = field(default_factory=list)
    distinct_name_count_override: int | None = None


def init_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_NAME_CHAR_STATS)
    for sql in INDEXES:
        conn.execute(sql)
    conn.commit()


def seed_records() -> list[NameRecord]:
    records = []
    for full_name, _surname, given_name, _category, _era, gender, _brief, fame_score in FAMOUS_NAMES:
        records.append(
            NameRecord(
                full_name=full_name,
                given_name=given_name,
                gender=normalize_gender(gender),
                fame_score=int(fame_score),
                source="famous_seed",
            )
        )
    return records


def wikidata_records(jsonl_path: Path) -> list[NameRecord]:
    records: list[NameRecord] = []
    if not jsonl_path.exists():
        return records
    with jsonl_path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            full_name = clean_full_name(raw.get("label_zh", ""))
            if not is_chinese(full_name) or len(full_name) < 2 or len(full_name) > 6:
                continue
            split = split_chinese_name(full_name)
            if not split:
                continue
            _surname, given_name = split
            if not is_valid_given_name(given_name):
                continue
            records.append(
                NameRecord(
                    full_name=full_name,
                    given_name=given_name,
                    gender=normalize_gender(map_gender(raw.get("gender_label"))),
                    fame_score=fame_from_sitelinks(int(raw.get("sitelinks", 8))),
                    source="wikidata",
                )
            )
    return records


def chinapis_stats(csv_path: Path) -> dict[str, CharStat]:
    stats: dict[str, CharStat] = {}
    if not csv_path.exists():
        return stats
    with csv_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            char = (row.get("character") or "").strip()
            if len(char) != 1 or not is_chinese(char):
                continue
            male_count = int(float(row.get("n.male") or 0))
            female_count = int(float(row.get("n.female") or 0))
            total_count = male_count + female_count
            stat = stats.setdefault(char, CharStat(char=char))
            stat.total_count += total_count
            stat.distinct_name_count_override = (
                (stat.distinct_name_count_override or 0) + total_count
            )
            stat.male_count += male_count
            stat.female_count += female_count
            stat.sources.add("chinapis_given_name_df")
    return stats


def normalize_gender(value: str | None) -> str:
    if value == "男":
        return "男"
    if value == "女":
        return "女"
    return "未知"


def is_valid_given_name(given_name: str) -> bool:
    return bool(given_name) and len(given_name) <= 3 and is_chinese(given_name)


def split_chinese_name(full_name: str) -> tuple[str, str] | None:
    if len(full_name) >= 3 and full_name[:2] in COMPOUND_CHINESE_SURNAMES:
        return full_name[:2], full_name[2:]
    if len(full_name) >= 2 and full_name[0] in COMMON_CHINESE_SURNAMES:
        return full_name[0], full_name[1:]
    return None


def aggregate(records: Iterable[NameRecord]) -> dict[str, CharStat]:
    stats: dict[str, CharStat] = {}
    seen_records: set[tuple[str, str, str]] = set()
    for record in records:
        if not is_valid_given_name(record.given_name):
            continue
        key = (record.full_name, record.given_name, record.source)
        if key in seen_records:
            continue
        seen_records.add(key)

        for index, char in enumerate(record.given_name):
            stat = stats.setdefault(char, CharStat(char=char))
            stat.total_count += 1
            stat.names.add(record.full_name)
            if record.gender == "男":
                stat.male_count += 1
            elif record.gender == "女":
                stat.female_count += 1
            else:
                stat.unknown_gender_count += 1
            if index == 0:
                stat.position_1_count += 1
            elif index == 1:
                stat.position_2_count += 1
            else:
                stat.position_other_count += 1
            stat.weighted_fame += max(0, int(record.fame_score))
            stat.sources.add(record.source)
            if len(stat.sample_names) < 8 and record.full_name not in stat.sample_names:
                stat.sample_names.append(record.full_name)
    return stats


def serialize_stats(stats: dict[str, CharStat]) -> list[dict]:
    rows = []
    for stat in sorted(stats.values(), key=lambda item: (-item.total_count, item.char)):
        rows.append(
            {
                "char": stat.char,
                "total_count": stat.total_count,
                "distinct_name_count": (
                    stat.distinct_name_count_override
                    if stat.distinct_name_count_override is not None
                    else len(stat.names)
                ),
                "male_count": stat.male_count,
                "female_count": stat.female_count,
                "unknown_gender_count": stat.unknown_gender_count,
                "position_1_count": stat.position_1_count,
                "position_2_count": stat.position_2_count,
                "position_other_count": stat.position_other_count,
                "weighted_fame": stat.weighted_fame,
                "source_count": len(stat.sources),
                "sources": json.dumps(sorted(stat.sources), ensure_ascii=False),
                "sample_names": json.dumps(stat.sample_names, ensure_ascii=False),
            }
        )
    return rows


def import_stats(conn: sqlite3.Connection, rows: list[dict]) -> int:
    init_sqlite(conn)
    with conn:
        conn.execute("DELETE FROM name_char_stats")
        conn.executemany(UPSERT_STAT, rows)
    return len(rows)


def build_records(source: str, wikidata_jsonl: Path) -> list[NameRecord]:
    records: list[NameRecord] = []
    if source in ("seed", "all"):
        records.extend(seed_records())
    if source in ("wikidata", "all"):
        records.extend(wikidata_records(wikidata_jsonl))
    return records


def merge_stats(base: dict[str, CharStat], extra: dict[str, CharStat]) -> dict[str, CharStat]:
    for char, incoming in extra.items():
        stat = base.setdefault(char, CharStat(char=char))
        stat.total_count += incoming.total_count
        stat.names.update(incoming.names)
        stat.male_count += incoming.male_count
        stat.female_count += incoming.female_count
        stat.unknown_gender_count += incoming.unknown_gender_count
        stat.position_1_count += incoming.position_1_count
        stat.position_2_count += incoming.position_2_count
        stat.position_other_count += incoming.position_other_count
        stat.weighted_fame += incoming.weighted_fame
        stat.sources.update(incoming.sources)
        for name in incoming.sample_names:
            if len(stat.sample_names) >= 8:
                break
            if name not in stat.sample_names:
                stat.sample_names.append(name)
        if incoming.distinct_name_count_override is not None:
            stat.distinct_name_count_override = (
                (stat.distinct_name_count_override or 0)
                + incoming.distinct_name_count_override
            )
    return base


def build_stats(source: str, wikidata_jsonl: Path, chinapis_csv: Path) -> tuple[dict[str, CharStat], int]:
    record_source = "all" if source == "all" else source
    if source == "chinapis":
        records: list[NameRecord] = []
    else:
        records = build_records(record_source, wikidata_jsonl)

    stats = aggregate(records)
    if source in ("chinapis", "all"):
        merge_stats(stats, chinapis_stats(chinapis_csv))
    return stats, len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build given-name character statistics")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--source", choices=["seed", "wikidata", "chinapis", "all"], default="all")
    parser.add_argument("--wikidata-jsonl", type=Path, default=DEFAULT_WIKIDATA_JSONL)
    parser.add_argument("--chinapis-csv", type=Path, default=DEFAULT_CHINAPIS_CSV)
    args = parser.parse_args()

    stats, record_count = build_stats(args.source, args.wikidata_jsonl, args.chinapis_csv)
    rows = serialize_stats(stats)
    args.sqlite.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.sqlite) as conn:
        count = import_stats(conn, rows)

    print(f"Imported {count} given-name characters from {record_count} names -> {args.sqlite}")


if __name__ == "__main__":
    main()
