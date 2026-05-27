"""
验证名人库导入质量。

输出：
- 总览：总数、按朝代/类别/性别/来源分布
- 抽样：随机 20 位名人，展示完整记录 + 该名所有字的反向索引
- 数据健康：缺失 era/category/birth_year 比例；fame_score 分布
- 反向索引：top 10 高频字（按 famous_count）
"""
from __future__ import annotations

import argparse
import random
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def stats(conn: sqlite3.Connection) -> None:
    section("总览")
    total = conn.execute("SELECT COUNT(*) FROM famous_names").fetchone()[0]
    print(f"famous_names 总数: {total}")
    idx_total = conn.execute("SELECT COUNT(*) FROM character_famous").fetchone()[0]
    chars_covered = conn.execute("SELECT COUNT(DISTINCT char) FROM character_famous").fetchone()[0]
    print(f"character_famous 索引数: {idx_total}，覆盖单字: {chars_covered}")

    section("按朝代分布（top 12）")
    for era, n in conn.execute(
        "SELECT COALESCE(era,'未知'), COUNT(*) c FROM famous_names GROUP BY era ORDER BY c DESC LIMIT 12"
    ):
        print(f"  {era:>6}  {n}")

    section("按类别分布")
    for cat, n in conn.execute(
        "SELECT COALESCE(category,'未分类'), COUNT(*) c FROM famous_names GROUP BY category ORDER BY c DESC LIMIT 15"
    ):
        print(f"  {cat:>8}  {n}")

    section("按性别分布")
    for g, n in conn.execute("SELECT gender, COUNT(*) FROM famous_names GROUP BY gender"):
        print(f"  {g}  {n}")

    section("按来源分布")
    for s, n in conn.execute("SELECT source, COUNT(*) FROM famous_names GROUP BY source"):
        print(f"  {s}  {n}")

    section("数据健康")
    for label, sql in [
        ("缺 era", "SELECT COUNT(*) FROM famous_names WHERE era IS NULL OR era=''"),
        ("缺 category", "SELECT COUNT(*) FROM famous_names WHERE category IS NULL OR category=''"),
        ("缺 birth_year", "SELECT COUNT(*) FROM famous_names WHERE birth_year IS NULL"),
        ("缺 brief", "SELECT COUNT(*) FROM famous_names WHERE brief IS NULL OR brief=''"),
    ]:
        n = conn.execute(sql).fetchone()[0]
        pct = 100 * n / total if total else 0
        print(f"  {label}: {n} ({pct:.1f}%)")

    section("fame_score 分位")
    for q, sql in [
        ("min", "SELECT MIN(fame_score) FROM famous_names"),
        ("p25", "SELECT fame_score FROM famous_names ORDER BY fame_score LIMIT 1 OFFSET (SELECT COUNT(*)/4 FROM famous_names)"),
        ("median", "SELECT fame_score FROM famous_names ORDER BY fame_score LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM famous_names)"),
        ("p75", "SELECT fame_score FROM famous_names ORDER BY fame_score LIMIT 1 OFFSET (3*(SELECT COUNT(*)/4 FROM famous_names))"),
        ("max", "SELECT MAX(fame_score) FROM famous_names"),
    ]:
        v = conn.execute(sql).fetchone()[0]
        print(f"  {q}: {v}")

    section("top 单字（按 famous_count 倒序，仅显示字库已收录的）")
    rows = conn.execute(
        """
        SELECT char, famous_count FROM characters
        WHERE famous_count > 0
        ORDER BY famous_count DESC LIMIT 15
        """
    ).fetchall()
    for ch, c in rows:
        print(f"  {ch}  {c}")


def sample(conn: sqlite3.Connection, n: int, seed: int) -> None:
    section(f"随机抽样 {n} 位名人")
    rng = random.Random(seed)
    total = conn.execute("SELECT COUNT(*) FROM famous_names").fetchone()[0]
    if total == 0:
        print("(库为空)")
        return
    sample_ids = rng.sample(range(1, total + 1), min(n, total))
    rows = conn.execute(
        f"""
        SELECT name_id, full_name, surname, given_name, category, era,
               birth_year, gender, fame_score, source, brief
        FROM famous_names
        WHERE name_id IN ({','.join('?'*len(sample_ids))})
        ORDER BY fame_score DESC
        """,
        sample_ids,
    ).fetchall()
    for row in rows:
        (name_id, full_name, surname, given, cat, era, birth, gender,
         fame, source, brief) = row
        brief = (brief or "")[:50]
        print(f"\n[{name_id}] {full_name}  surname={surname} given={given}")
        print(f"  类别={cat} 朝代={era} 出生={birth} 性别={gender} fame={fame} source={source}")
        if brief:
            print(f"  简介={brief}")
        chars = conn.execute(
            "SELECT char, position FROM character_famous WHERE name_id=? ORDER BY position",
            (name_id,),
        ).fetchall()
        print(f"  反查字索引: {chars}")


def main() -> None:
    parser = argparse.ArgumentParser(description="验证名人库导入")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    parser.add_argument("--sample-n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.sqlite.exists():
        sys.exit(f"找不到 SQLite：{args.sqlite}")

    with sqlite3.connect(args.sqlite) as conn:
        stats(conn)
        sample(conn, args.sample_n, args.seed)


if __name__ == "__main__":
    main()
