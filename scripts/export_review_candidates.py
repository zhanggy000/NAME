"""
导出待人工校对的单字 CSV。

筛选规则：
- wuxing_confidence < 60  → 即 Unihan 批量入库、偏旁兜底的低置信度字
- 排除已在 reviewed_top1000.json 里的字

排序规则（先文化优先级，后笔画）：
- classics_count + famous_count DESC  → 在典籍/名人中出现越多越优先校对
- kangxi_strokes ASC                  → 笔画少的更常用

用法：
    python scripts/export_review_candidates.py --limit 1000 \
        --sqlite data/name.db --out data/raw/review_candidates.csv

输出 CSV 列与 reviewed_top1000.json 字段对齐，可直接填完后人工或脚本转回 JSON。
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

REVIEW_JSON = ROOT / "data" / "seed" / "reviewed_top1000.json"

QUERY = """
SELECT char, pinyin, kangxi_strokes, wuxing, wuxing_confidence, radical,
       meaning_primary, gender_pref, classics_count, famous_count, data_source
FROM characters
WHERE wuxing_confidence < :threshold
ORDER BY (classics_count + famous_count) DESC, kangxi_strokes ASC, char ASC
LIMIT :limit
"""

CSV_FIELDS = [
    "char", "pinyin", "kangxi_strokes", "radical",
    "current_wuxing", "current_confidence", "current_meaning",
    "classics_count", "famous_count", "data_source",
    # 待填字段
    "wuxing", "wuxing_confidence", "gender_pref", "meaning",
    "style_tags", "reviewer", "reviewed_at", "notes",
]


def load_already_reviewed() -> set[str]:
    if not REVIEW_JSON.exists():
        return set()
    payload = json.loads(REVIEW_JSON.read_text(encoding="utf-8"))
    reviews = payload.get("reviews", []) if isinstance(payload, dict) else payload
    return {row["char"] for row in reviews}


def export(sqlite_path: Path, out_path: Path, limit: int, threshold: int) -> int:
    skip = load_already_reviewed()
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(QUERY, {"limit": limit + len(skip), "threshold": threshold}).fetchall()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            if row["char"] in skip:
                continue
            writer.writerow({
                "char": row["char"],
                "pinyin": row["pinyin"],
                "kangxi_strokes": row["kangxi_strokes"],
                "radical": row["radical"] or "",
                "current_wuxing": row["wuxing"],
                "current_confidence": row["wuxing_confidence"],
                "current_meaning": row["meaning_primary"],
                "classics_count": row["classics_count"],
                "famous_count": row["famous_count"],
                "data_source": row["data_source"],
                "wuxing": "",
                "wuxing_confidence": "",
                "gender_pref": "",
                "meaning": "",
                "style_tags": "",
                "reviewer": "",
                "reviewed_at": "",
                "notes": "",
            })
            written += 1
            if written >= limit:
                break
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="导出待校对单字 CSV")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "review_candidates.csv")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--threshold", type=int, default=60,
                        help="wuxing_confidence < threshold 视为待校对，默认 60")
    args = parser.parse_args()

    if not args.sqlite.exists():
        sys.exit(f"找不到 SQLite：{args.sqlite}，请先跑 scripts/import_characters.py")

    count = export(args.sqlite, args.out, args.limit, args.threshold)
    print(f"已导出 {count} 条待校对单字 → {args.out}")


if __name__ == "__main__":
    main()
