import sqlite3

from scripts.import_classics import import_classics, init_sqlite
from scripts.validate_classics import sample_indexed_chars, validate_chars


def test_validate_chars_accepts_valid_reverse_index():
    with sqlite3.connect(":memory:") as conn:
        init_sqlite(conn)
        import_classics(conn, [
            ("唐诗", "李白·静夜思", "床前明月光，疑是地上霜。", "唐", "李白"),
        ])

        chars = sample_indexed_chars(conn, sample_size=3, seed=1)
        failures = validate_chars(conn, chars)

    assert chars
    assert failures == []


def test_validate_chars_reports_missing_char_in_line():
    with sqlite3.connect(":memory:") as conn:
        init_sqlite(conn)
        import_classics(conn, [
            ("唐诗", "李白·静夜思", "床前明月光，疑是地上霜。", "唐", "李白"),
        ])
        conn.execute("UPDATE character_classics SET char = '海' WHERE char = '月'")

        failures = validate_chars(conn, ["海"])

    assert failures[0]["reason"] == "char_missing_in_line"
