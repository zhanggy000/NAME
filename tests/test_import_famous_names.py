import sqlite3

from scripts.import_famous_names import import_famous_names, init_sqlite


def test_import_famous_names_builds_reverse_index():
    rows = [
        ("刘诗雯", "刘", "诗雯", "运动员", "现代", "女", "乒乓球世界冠军", 85),
        ("李白", "李", "白", "诗人", "唐", "男", "诗仙", 100),
    ]

    with sqlite3.connect(":memory:") as conn:
        init_sqlite(conn)
        assert import_famous_names(conn, rows) == 2
        assert import_famous_names(conn, rows) == 2

        famous_count = conn.execute("SELECT COUNT(*) FROM famous_names").fetchone()[0]
        wen_refs = conn.execute(
            """
            SELECT f.full_name, f.fame_score
            FROM character_famous cf
            JOIN famous_names f ON f.name_id = cf.name_id
            WHERE cf.char = '雯'
            """
        ).fetchall()

    assert famous_count == 2
    assert wen_refs == [("刘诗雯", 85)]
