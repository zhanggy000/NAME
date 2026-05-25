"""名人库导入工具。"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from famous_names_corpus import FAMOUS_NAMES  # noqa: E402


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
    full_name, surname, given_name, category, era, gender, brief, fame_score, source
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(full_name, era, category) DO UPDATE SET
    surname = excluded.surname,
    given_name = excluded.given_name,
    gender = excluded.gender,
    brief = excluded.brief,
    fame_score = excluded.fame_score,
    source = excluded.source
RETURNING name_id;
"""


def init_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_FAMOUS_TABLE)
    conn.execute(CREATE_CHARACTER_FAMOUS_TABLE)
    for sql in INDEXES:
        conn.execute(sql)
    conn.commit()


def import_famous_names(conn: sqlite3.Connection, rows: list[tuple], source: str = "famous_seed") -> int:
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for full_name, surname, given_name, category, era, gender, brief, fame_score in rows:
            name_id = conn.execute(
                UPSERT_FAMOUS,
                (full_name, surname, given_name, category, era, gender, brief, fame_score, source),
            ).fetchone()[0]
            conn.execute("DELETE FROM character_famous WHERE name_id = ?", (name_id,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO character_famous (char, name_id, position)
                VALUES (?, ?, ?)
                """,
                [(char, name_id, index) for index, char in enumerate(given_name)],
            )

        if _table_exists(conn, "characters") and _column_exists(conn, "characters", "famous_count"):
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
    return len(rows)


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
    args = parser.parse_args()

    with sqlite3.connect(args.sqlite) as conn:
        init_sqlite(conn)
        count = import_famous_names(conn, FAMOUS_NAMES)
    print(f"已导入/更新 {count} 位名人 → {args.sqlite}")


if __name__ == "__main__":
    main()
