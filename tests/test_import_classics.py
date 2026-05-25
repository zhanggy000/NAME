import sqlite3

from scripts.import_classics import import_classics, init_sqlite, iter_unique_chars


def test_iter_unique_chars_skips_punctuation_and_duplicates():
    assert iter_unique_chars("明月明。") == [("明", 0), ("月", 1)]


def test_import_classics_builds_reverse_index():
    rows = [
        ("唐诗", "李白·静夜思", "床前明月光，疑是地上霜。", "唐", "李白"),
        ("楚辞", "离骚", "扈江离与辟芷兮，纫秋兰以为佩。", "先秦", "屈原"),
    ]

    with sqlite3.connect(":memory:") as conn:
        init_sqlite(conn)
        assert import_classics(conn, rows) == 2
        assert import_classics(conn, rows) == 2

        classics_count = conn.execute("SELECT COUNT(*) FROM classics").fetchone()[0]
        ming_refs = conn.execute(
            """
            SELECT c.book, c.chapter, c.line_text
            FROM character_classics cc
            JOIN classics c ON c.ref_id = cc.ref_id
            WHERE cc.char = '明'
            """
        ).fetchall()
        lan_refs = conn.execute(
            "SELECT COUNT(*) FROM character_classics WHERE char = '兰'"
        ).fetchone()[0]

    assert classics_count == 2
    assert ming_refs == [("唐诗", "李白·静夜思", "床前明月光，疑是地上霜。")]
    assert lan_refs == 1
