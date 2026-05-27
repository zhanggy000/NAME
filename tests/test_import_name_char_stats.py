import json
import sqlite3

from scripts.import_name_char_stats import (
    NameRecord,
    aggregate,
    chinapis_stats,
    import_stats,
    merge_stats,
    serialize_stats,
    split_chinese_name,
)


def test_aggregate_counts_gender_position_and_sources():
    records = [
        NameRecord("刘诗雯", "诗雯", "女", 85, "seed"),
        NameRecord("李白", "白", "男", 100, "seed"),
        NameRecord("王诗文", "诗文", "男", 70, "wikidata"),
        NameRecord("王诗文", "诗文", "男", 70, "wikidata"),
    ]

    rows = {row["char"]: row for row in serialize_stats(aggregate(records))}

    assert rows["诗"]["total_count"] == 2
    assert rows["诗"]["distinct_name_count"] == 2
    assert rows["诗"]["male_count"] == 1
    assert rows["诗"]["female_count"] == 1
    assert rows["诗"]["position_1_count"] == 2
    assert rows["诗"]["position_2_count"] == 0
    assert rows["诗"]["weighted_fame"] == 155
    assert json.loads(rows["诗"]["sources"]) == ["seed", "wikidata"]
    assert json.loads(rows["诗"]["sample_names"]) == ["刘诗雯", "王诗文"]

    assert rows["雯"]["female_count"] == 1
    assert rows["雯"]["position_2_count"] == 1
    assert rows["白"]["male_count"] == 1


def test_import_stats_rebuilds_sqlite_table():
    rows = serialize_stats(
        aggregate(
            [
                NameRecord("刘诗雯", "诗雯", "女", 85, "seed"),
                NameRecord("王诗文", "诗文", "男", 70, "wikidata"),
            ]
        )
    )

    with sqlite3.connect(":memory:") as conn:
        assert import_stats(conn, rows) == 3
        assert import_stats(conn, rows[:1]) == 1
        stored = conn.execute(
            """
            SELECT char, total_count, source_count, sample_names
            FROM name_char_stats
            ORDER BY char
            """
        ).fetchall()

    assert stored == [("诗", 2, 2, '["刘诗雯", "王诗文"]')]


def test_split_chinese_name_rejects_obvious_transliterations():
    assert split_chinese_name("刘诗雯") == ("刘", "诗雯")
    assert split_chinese_name("欧阳修") == ("欧阳", "修")
    assert split_chinese_name("奥古斯都") is None
    assert split_chinese_name("岸田文雄") is None


def test_chinapis_stats_merge_frequency_counts(tmp_path):
    csv_path = tmp_path / "given_name.csv"
    csv_path.write_text(
        "character,pinyin,bihua,n.male,n.female\n"
        "雯,wen,12,10,90\n"
        "诗,shi,8,30,70\n",
        encoding="utf-8",
    )

    stats = aggregate([NameRecord("刘诗雯", "诗雯", "女", 85, "seed")])
    merge_stats(stats, chinapis_stats(csv_path))
    rows = {row["char"]: row for row in serialize_stats(stats)}

    assert rows["雯"]["total_count"] == 101
    assert rows["雯"]["female_count"] == 91
    assert rows["雯"]["male_count"] == 10
    assert rows["雯"]["distinct_name_count"] == 100
    assert json.loads(rows["雯"]["sources"]) == ["chinapis_given_name_df", "seed"]
