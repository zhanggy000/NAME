"""
从 Wikidata 名人给定名里挖出"真实取名常用字"，自动生成 Top1000 评审条目。

数据流：
  data/name.db (character_famous)     ← 真实名用字 + 频次
       +
  data/raw/Unihan.zip                  ← 笔画 / 偏旁 / 拼音兜底
       │
       ▼  scripts/bootstrap_naming_chars.py
       │  ├─ 字频统计（在给定名里出现次数）
       │  ├─ 性别偏好（女名比例 → gender_pref）
       │  ├─ 五行兜底（偏旁映射）
       │  ├─ 拼音（pypinyin）
       │  ├─ 笔画（Unihan kTotalStrokes）
       │  └─ 标注 review_status="auto_bootstrap" 以便人工后续审校
       ▼
  data/seed/reviewed_top1000.json (新增 reviews 数组)
       │  python scripts/import_characters.py --source seed
       │  python scripts/apply_reviews.py
       ▼
  characters 表自动扩到 ~1000+ 行
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from chinese_surnames import is_chinese_surname  # noqa: E402

# 复用 import_characters 里的偏旁→五行映射，避免重复
sys.path.insert(0, str(ROOT / "scripts"))
from import_characters import RADICAL_WUXING, PINYIN_TONE_MARKS  # noqa: E402

DEFAULT_DB = ROOT / "data" / "name.db"
DEFAULT_UNIHAN = ROOT / "data" / "raw" / "Unihan.zip"
DEFAULT_REVIEW_JSON = ROOT / "data" / "seed" / "reviewed_top1000.json"


# ============================================================
# Unihan 解析（笔画 + 偏旁）
# ============================================================

def load_unihan(zip_path: Path) -> dict[str, dict]:
    """返回 {char: {kangxi, radical_no}}。"""
    if not zip_path.exists():
        print(f"⚠ 找不到 Unihan.zip：{zip_path}，笔画/偏旁字段将留空", file=sys.stderr)
        return {}
    strokes: dict[str, int] = {}
    radicals: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for raw in zf.open("Unihan_IRGSources.txt"):
            line = raw.decode("utf-8").strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            code, field, value = parts
            if field == "kTotalStrokes":
                strokes[code] = int(value.split()[0])
            elif field == "kRSUnicode":
                radicals[code] = value.split(".")[0].strip("'")
    out: dict[str, dict] = {}
    for code, k in strokes.items():
        cp = int(code[2:], 16)
        if not 0x4E00 <= cp <= 0x9FFF:
            continue
        out[chr(cp)] = {
            "kangxi": k,
            "radical_no": radicals.get(code),
        }
    return out


# ============================================================
# 字频 + 性别比例 + 名人代表
# ============================================================

def collect_char_stats(db_path: Path) -> dict[str, dict]:
    """从 character_famous + famous_names 聚合每个字的取名统计。

    返回：{char: {count, female_count, male_count, top_names: [...]}}
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT cf.char, f.full_name, f.given_name, f.gender, f.fame_score, f.era
            FROM character_famous cf
            JOIN famous_names f ON f.name_id = cf.name_id
            """
        ).fetchall()

    stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "female_count": 0, "male_count": 0,
        "top_names": [],  # (fame_score, full_name, era)
    })
    for r in rows:
        ch = r["char"]
        if not ch or len(ch) != 1:
            continue
        # 必须出现在给定名（不算姓氏部分）
        if ch not in (r["given_name"] or ""):
            continue
        d = stats[ch]
        d["count"] += 1
        if r["gender"] == "女":
            d["female_count"] += 1
        elif r["gender"] == "男":
            d["male_count"] += 1
        d["top_names"].append((r["fame_score"], r["full_name"], r["era"]))

    # 留前 3 个最知名的作为 famous_refs
    for ch, d in stats.items():
        # 用 fame_score 倒序（None 视为 0），name/era 作为 tie-breaker
        d["top_names"].sort(key=lambda t: (-(t[0] or 0), t[1] or "", t[2] or ""))
        d["top_names"] = d["top_names"][:3]

    return dict(stats)


# ============================================================
# 推断字段
# ============================================================

def infer_gender(female: int, male: int) -> str:
    total = female + male
    if total < 5:
        return "中性"
    ratio = female / total
    if ratio >= 0.75:
        return "女"
    if ratio <= 0.25:
        return "男"
    return "中性"


def infer_wuxing(radical_no: str | None) -> tuple[str, int]:
    """返回 (五行, 置信度)。无偏旁时土+30 兜底。"""
    if not radical_no:
        return "土", 30
    wx_tuple = RADICAL_WUXING.get(radical_no)
    if not wx_tuple:
        return "土", 30
    return wx_tuple[0], wx_tuple[2]


def get_pinyin(ch: str) -> tuple[str, int]:
    from pypinyin import pinyin, Style
    try:
        marked = pinyin(ch, style=Style.TONE, errors="ignore")
        if not marked or not marked[0]:
            return "", 5
    except Exception:
        return "", 5
    text = marked[0][0]
    tone = 5
    for c in text:
        if c in PINYIN_TONE_MARKS:
            tone = PINYIN_TONE_MARKS[c][1]
            break
    return text, tone


# ============================================================
# 排除规则：常见姓氏字 / 已有 seed 字 / 单笔划兜底字
# ============================================================

SURNAME_FAMOUS_GUARD_THRESHOLD = 0.85  # 给定名里出现率 > 0.85 才纳入（避免姓氏混淆）


def is_likely_surname_only(ch: str, db_path: Path) -> bool:
    """该字几乎总作姓氏出现 → 排除。"""
    with sqlite3.connect(db_path) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM famous_names WHERE full_name LIKE ?", (f"%{ch}%",)
        ).fetchone()[0]
        as_surname = conn.execute(
            "SELECT COUNT(*) FROM famous_names WHERE surname LIKE ?", (f"%{ch}%",)
        ).fetchone()[0]
    if total == 0:
        return False
    return (total - as_surname) / total < (1 - SURNAME_FAMOUS_GUARD_THRESHOLD)


# ============================================================
# 主流程
# ============================================================

def build_entries(
    stats: dict[str, dict],
    unihan: dict[str, dict],
    top_n: int,
    db_path: Path,
    existing_chars: set[str],
) -> list[dict]:
    # 按 count 倒序
    candidates = sorted(stats.items(), key=lambda kv: -kv[1]["count"])

    entries: list[dict] = []
    skipped_surname = 0
    skipped_existing = 0
    for ch, d in candidates:
        if len(entries) >= top_n:
            break
        if ch in existing_chars:
            skipped_existing += 1
            continue
        # 仅作姓氏的字跳过
        ok_surname, _, _ = is_chinese_surname(ch)
        if ok_surname and is_likely_surname_only(ch, db_path):
            skipped_surname += 1
            continue

        unihan_row = unihan.get(ch, {})
        kangxi = unihan_row.get("kangxi")
        radical = unihan_row.get("radical_no")
        wuxing, wx_conf = infer_wuxing(radical)
        pinyin, tone = get_pinyin(ch)
        gender = infer_gender(d["female_count"], d["male_count"])

        if not kangxi or not pinyin:
            # 数据不全的跳过（笔画或拼音缺失会影响后续评分）
            continue

        famous_refs = [
            f"{name}（{era or '？'}）" for _fs, name, era in d["top_names"]
        ]

        entries.append({
            "char": ch,
            "pinyin": pinyin,
            "tone": tone,
            "kangxi": kangxi,
            "simplified": kangxi,  # 兜底相同
            "radical": str(radical) if radical else None,
            "wuxing": wuxing,
            "wuxing_confidence": max(wx_conf, 50),  # bootstrap 标记为中低置信
            "gender_pref": gender,
            "meaning": f"自动引导：在 {d['count']} 位中国名人的名字中出现",
            "style_tags": ["自动引导", "待人工复审"],
            "classics_refs": [],
            "famous_refs": famous_refs,
            "reviewer": "auto_bootstrap_v1",
            "reviewed_at": "2026-05-27",
            "notes": (
                f"频次 {d['count']}, 男 {d['male_count']}, 女 {d['female_count']}; "
                f"代表名人: {', '.join(n for _, n, _ in d['top_names'])}"
            ),
        })

    print(f"已生成 {len(entries)} 条 bootstrap 评审条目（跳过已存在 {skipped_existing}，跳过纯姓氏 {skipped_surname}）",
          file=sys.stderr)
    return entries


def load_existing_chars(db_path: Path) -> set[str]:
    """已经在 characters 表 + reviewed_top1000.json 里的字都跳过。"""
    chars: set[str] = set()
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            for (ch,) in conn.execute("SELECT char FROM characters"):
                chars.add(ch)
    if DEFAULT_REVIEW_JSON.exists():
        payload = json.loads(DEFAULT_REVIEW_JSON.read_text(encoding="utf-8"))
        reviews = payload.get("reviews", []) if isinstance(payload, dict) else payload
        chars.update(r["char"] for r in reviews if r.get("char"))
    return chars


def merge_into_reviews(entries: list[dict]) -> None:
    if DEFAULT_REVIEW_JSON.exists():
        payload = json.loads(DEFAULT_REVIEW_JSON.read_text(encoding="utf-8"))
    else:
        payload = {"version": 1, "description": "", "reviews": []}
    reviews = payload.get("reviews", []) if isinstance(payload, dict) else []
    by_char = {r["char"]: r for r in reviews}
    for entry in entries:
        # 不覆盖已有的人工评审（reviewer != auto_bootstrap_v1 视为人工）
        existing = by_char.get(entry["char"])
        if existing and existing.get("reviewer") not in (None, "", "auto_bootstrap_v1"):
            continue
        by_char[entry["char"]] = entry
    new_reviews = sorted(by_char.values(), key=lambda r: r["char"])
    payload["reviews"] = new_reviews
    DEFAULT_REVIEW_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"reviewed_top1000.json 总计 {len(new_reviews)} 条", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="从 Wikidata 名人挖出 Top 取名字并生成 bootstrap 评审")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_DB)
    parser.add_argument("--unihan-zip", type=Path, default=DEFAULT_UNIHAN)
    parser.add_argument("--top-n", type=int, default=1000)
    args = parser.parse_args()

    if not args.sqlite.exists():
        sys.exit(f"找不到 SQLite：{args.sqlite}")

    print("→ 读 Unihan ...", file=sys.stderr)
    unihan = load_unihan(args.unihan_zip)
    print(f"  Unihan 笔画字典: {len(unihan)} 字", file=sys.stderr)

    print("→ 统计 character_famous 字频 ...", file=sys.stderr)
    stats = collect_char_stats(args.sqlite)
    print(f"  唯一字: {len(stats)}", file=sys.stderr)

    existing = load_existing_chars(args.sqlite)
    print(f"  已有字（characters 表 + reviewed_top1000.json）: {len(existing)}", file=sys.stderr)

    entries = build_entries(stats, unihan, args.top_n, args.sqlite, existing)
    merge_into_reviews(entries)


if __name__ == "__main__":
    main()
