"""验证典籍反向索引准确性。"""
from __future__ import annotations

import argparse
import random
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sample_indexed_chars(conn: sqlite3.Connection, sample_size: int, seed: int) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT char FROM character_classics ORDER BY char"
    ).fetchall()
    chars = [row[0] for row in rows]
    rng = random.Random(seed)
    if sample_size >= len(chars):
        return chars
    return rng.sample(chars, sample_size)


def validate_chars(conn: sqlite3.Connection, chars: list[str]) -> list[dict]:
    failures = []
    for char in chars:
        rows = conn.execute(
            """
            SELECT c.book, c.chapter, c.line_text
            FROM character_classics cc
            JOIN classics c ON c.ref_id = cc.ref_id
            WHERE cc.char = ?
            """,
            (char,),
        ).fetchall()
        if not rows:
            failures.append({"char": char, "reason": "no_refs"})
            continue
        for book, chapter, line in rows:
            if char not in line:
                failures.append({
                    "char": char,
                    "reason": "char_missing_in_line",
                    "book": book,
                    "chapter": chapter,
                    "line": line,
                })
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="随机验证典籍字句反向索引")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260525)
    args = parser.parse_args()

    with sqlite3.connect(args.sqlite) as conn:
        chars = sample_indexed_chars(conn, args.sample_size, args.seed)
        failures = validate_chars(conn, chars)

    if failures:
        for failure in failures:
            print(f"失败：{failure}")
        raise SystemExit(1)

    print(f"验证通过：抽查 {len(chars)} 个字，反向索引均命中真实句子")


if __name__ == "__main__":
    main()
