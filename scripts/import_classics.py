"""典籍语料导入工具。"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from classics_corpus import CLASSICS_CORPUS  # noqa: E402


CREATE_CLASSICS_TABLE = """
CREATE TABLE IF NOT EXISTS classics (
    ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book TEXT NOT NULL,
    chapter TEXT,
    section TEXT,
    line_text TEXT NOT NULL,
    translation TEXT,
    annotation TEXT,
    line_index INTEGER,
    era TEXT,
    author TEXT,
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book, chapter, line_text)
);
"""


CREATE_CHARACTER_CLASSICS_TABLE = """
CREATE TABLE IF NOT EXISTS character_classics (
    char TEXT NOT NULL,
    ref_id INTEGER NOT NULL,
    position INTEGER,
    is_keyword INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (char, ref_id),
    FOREIGN KEY (ref_id) REFERENCES classics(ref_id) ON DELETE CASCADE
);
"""


INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_classics_book ON classics (book)",
    "CREATE INDEX IF NOT EXISTS idx_classics_book_chapter ON classics (book, chapter)",
    "CREATE INDEX IF NOT EXISTS idx_character_classics_char ON character_classics (char)",
    "CREATE INDEX IF NOT EXISTS idx_character_classics_ref ON character_classics (ref_id)",
]


UPSERT_CLASSIC = """
INSERT INTO classics (book, chapter, line_text, era, author, data_source)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(book, chapter, line_text) DO UPDATE SET
    era = excluded.era,
    author = excluded.author,
    data_source = excluded.data_source
RETURNING ref_id;
"""


def is_cjk_char(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def iter_unique_chars(line: str) -> list[tuple[str, int]]:
    seen = set()
    pairs = []
    for index, char in enumerate(line):
        if not is_cjk_char(char) or char in seen:
            continue
        seen.add(char)
        pairs.append((char, index))
    return pairs


def init_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_CLASSICS_TABLE)
    conn.execute(CREATE_CHARACTER_CLASSICS_TABLE)
    for sql in INDEXES:
        conn.execute(sql)
    conn.commit()


def import_classics(conn: sqlite3.Connection, rows: list[tuple], data_source: str = "classics_seed") -> int:
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for book, chapter, line, era, author in rows:
            ref_id = conn.execute(
                UPSERT_CLASSIC,
                (book, chapter, line, era, author, data_source),
            ).fetchone()[0]
            conn.execute("DELETE FROM character_classics WHERE ref_id = ?", (ref_id,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO character_classics (char, ref_id, position, is_keyword)
                VALUES (?, ?, ?, 0)
                """,
                [(char, ref_id, position) for char, position in iter_unique_chars(line)],
            )

        if _table_exists(conn, "characters") and _column_exists(conn, "characters", "classics_count"):
            conn.execute("UPDATE characters SET classics_count = 0")
            conn.execute(
                """
                UPDATE characters
                SET classics_count = (
                    SELECT COUNT(*) FROM character_classics
                    WHERE character_classics.char = characters.char
                )
                WHERE char IN (SELECT DISTINCT char FROM character_classics)
                """
            )
    return len(rows)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    return any(row[1] == column_name for row in conn.execute(f"PRAGMA table_info({table_name})"))


def main() -> None:
    parser = argparse.ArgumentParser(description="导入典籍语料并建立单字反向索引")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "name.db")
    args = parser.parse_args()

    with sqlite3.connect(args.sqlite) as conn:
        init_sqlite(conn)
        count = import_classics(conn, CLASSICS_CORPUS)
    print(f"已导入/更新 {count} 条典籍语料 → {args.sqlite}")


if __name__ == "__main__":
    main()
