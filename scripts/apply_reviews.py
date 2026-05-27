"""
应用人工校对结果到 SQLite。

数据流：
  data/raw/review_candidates.csv (人工填好)
       │  python scripts/apply_reviews.py --merge-csv ...
       ▼
  data/seed/reviewed_top1000.json   ← git 持久化的校对成果
       │  python scripts/apply_reviews.py
       ▼
  data/name.db (characters 表的人工字段被覆盖)

reviewed_top1000.json 的单条 review 字段：
    char (必填)                 — 单个汉字
    wuxing (必填)               — 木/火/土/金/水
    wuxing_confidence (可选)    — 默认 95
    gender_pref (可选)          — 男/女/中性，默认"中性"
    meaning (必填)              — 取名释义（覆盖 Unihan 兜底文本）
    style_tags (可选)           — 字符串数组，如 ["古典","稳重"]
    classics_refs (可选)        — 关联典籍 id 数组
    famous_refs (可选)          — 关联名人 id 数组
    reviewer (可选)             — 校对人，便于追溯
    reviewed_at (可选)          — ISO 日期
    notes (可选)                — 自由备注
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_JSON = ROOT / "data" / "seed" / "reviewed_top1000.json"

VALID_WUXING = {"木", "火", "土", "金", "水"}
VALID_GENDER = {"男", "女", "中性"}

UPDATE_SQL = """
UPDATE characters
SET wuxing = :wuxing,
    wuxing_source = 'manual_review',
    wuxing_confidence = :wuxing_confidence,
    meaning_primary = :meaning,
    gender_pref = :gender_pref,
    style_tags = :style_tags,
    classics_refs = :classics_refs,
    famous_refs = :famous_refs,
    data_source = 'manual_review',
    updated_at = CURRENT_TIMESTAMP
WHERE char = :char
"""


def load_reviews() -> tuple[dict, list[dict]]:
    if not REVIEW_JSON.exists():
        return {"version": 1, "reviews": []}, []
    payload = json.loads(REVIEW_JSON.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"version": 1, "reviews": payload}, payload
    return payload, payload.get("reviews", [])


def save_reviews(payload: dict, reviews: list[dict]) -> None:
    payload["reviews"] = reviews
    REVIEW_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate(row: dict) -> list[str]:
    errs = []
    if not row.get("char") or len(row["char"]) != 1:
        errs.append(f"char 必须是单字: {row.get('char')!r}")
    if row.get("wuxing") not in VALID_WUXING:
        errs.append(f"{row.get('char')}: wuxing 非法 {row.get('wuxing')!r}")
    if row.get("gender_pref", "中性") not in VALID_GENDER:
        errs.append(f"{row.get('char')}: gender_pref 非法 {row['gender_pref']!r}")
    if not row.get("meaning"):
        errs.append(f"{row.get('char')}: meaning 不能为空")
    return errs


def normalize_for_db(row: dict) -> dict:
    return {
        "char": row["char"],
        "wuxing": row["wuxing"],
        "wuxing_confidence": int(row.get("wuxing_confidence", 95)),
        "meaning": row["meaning"],
        "gender_pref": row.get("gender_pref", "中性"),
        "style_tags": json.dumps(row.get("style_tags", []), ensure_ascii=False),
        "classics_refs": json.dumps(row.get("classics_refs", []), ensure_ascii=False),
        "famous_refs": json.dumps(row.get("famous_refs", []), ensure_ascii=False),
    }


def merge_csv(csv_path: Path) -> int:
    """把人工填完的 CSV 合并进 reviewed_top1000.json。"""
    payload, reviews = load_reviews()
    by_char = {r["char"]: r for r in reviews}
    added = 0
    today = date.today().isoformat()

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            if not raw.get("wuxing"):
                continue  # 未填的跳过
            entry = {
                "char": raw["char"],
                "wuxing": raw["wuxing"].strip(),
                "wuxing_confidence": int(raw["wuxing_confidence"] or 95),
                "gender_pref": (raw.get("gender_pref") or "中性").strip(),
                "meaning": raw["meaning"].strip(),
                "style_tags": [t.strip() for t in (raw.get("style_tags") or "").split("|") if t.strip()],
                "reviewer": raw.get("reviewer") or "",
                "reviewed_at": raw.get("reviewed_at") or today,
                "notes": raw.get("notes") or "",
            }
            errs = validate(entry)
            if errs:
                print("跳过:", *errs, sep="\n  ")
                continue
            by_char[entry["char"]] = entry
            added += 1

    new_reviews = sorted(by_char.values(), key=lambda r: r["char"])
    save_reviews(payload, new_reviews)
    print(f"已合并 {added} 条到 {REVIEW_JSON}（总计 {len(new_reviews)} 条）")
    return added


def apply_to_db(sqlite_path: Path) -> int:
    _payload, reviews = load_reviews()
    if not reviews:
        print("reviewed_top1000.json 为空，无需应用。")
        return 0

    all_errs: list[str] = []
    payloads = []
    for r in reviews:
        errs = validate(r)
        if errs:
            all_errs.extend(errs)
            continue
        payloads.append(normalize_for_db(r))

    if all_errs:
        print("校验失败，已中止：")
        for e in all_errs:
            print("  -", e)
        sys.exit(1)

    with sqlite3.connect(sqlite_path) as conn:
        cur = conn.cursor()
        affected = 0
        for p in payloads:
            cur.execute(UPDATE_SQL, p)
            affected += cur.rowcount
        conn.commit()
    print(f"已将 {len(payloads)} 条评审应用到 {sqlite_path}（影响 {affected} 行）")
    return affected


def main() -> None:
    parser = argparse.ArgumentParser(description="应用人工校对结果")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--merge-csv", type=Path, default=None,
                        help="先把这份 CSV 合并进 reviewed_top1000.json，再写库")
    args = parser.parse_args()

    if args.merge_csv:
        if not args.merge_csv.exists():
            sys.exit(f"找不到 CSV：{args.merge_csv}")
        merge_csv(args.merge_csv)

    if not args.sqlite.exists():
        sys.exit(f"找不到 SQLite：{args.sqlite}，请先跑 scripts/import_characters.py")
    apply_to_db(args.sqlite)


if __name__ == "__main__":
    main()
