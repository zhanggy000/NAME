"""生成单字人工校对清单。"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fetch_unreviewed(conn: sqlite3.Connection, limit: int) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            char, pinyin, tone, kangxi_strokes, simplified_strokes,
            wuxing, wuxing_source, wuxing_confidence, radical,
            gender_pref, meaning_primary, style_tags
        FROM characters
        WHERE wuxing_source != 'manual_review'
        ORDER BY
            CASE WHEN data_source = 'unihan_iicore' THEN 0 ELSE 1 END,
            wuxing_confidence ASC,
            char ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def write_review_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "char", "pinyin", "tone", "kangxi_strokes", "simplified_strokes",
        "wuxing", "wuxing_source", "wuxing_confidence", "radical",
        "gender_pref", "meaning_primary", "style_tags",
        "reviewed_wuxing", "reviewed_gender_pref", "review_note",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **row,
                "reviewed_wuxing": "",
                "reviewed_gender_pref": "",
                "review_note": "",
            })


def main() -> None:
    parser = argparse.ArgumentParser(description="生成单字人工校对 CSV")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "review" / "characters_top1000_review.csv",
    )
    args = parser.parse_args()

    with sqlite3.connect(args.sqlite) as conn:
        rows = fetch_unreviewed(conn, args.limit)
    write_review_csv(rows, args.output)
    print(f"已生成 {len(rows)} 条待校对单字 → {args.output}")


if __name__ == "__main__":
    main()
