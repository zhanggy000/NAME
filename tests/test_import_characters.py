import json
import sqlite3

from scripts.import_characters import import_characters, init_sqlite, normalize_character


def test_normalize_character_maps_seed_fields():
    row = normalize_character({
        "char": "雯",
        "pinyin": "wén",
        "tone": 2,
        "kangxi": 12,
        "simplified": 12,
        "wuxing": "水",
        "radical": "雨",
        "meaning": "有花纹的云彩",
        "gender_pref": "女",
        "style_tags": ["婉约", "清新"],
        "classics_refs": ["示例"],
    })

    assert row["char"] == "雯"
    assert row["kangxi_strokes"] == 12
    assert row["simplified_strokes"] == 12
    assert row["wuxing_source"] == "seed_manual"
    assert json.loads(row["style_tags"]) == ["婉约", "清新"]
    assert json.loads(row["classics_refs"]) == ["示例"]


def test_import_characters_upserts_rows():
    rows = [
        {
            "char": "雯",
            "pinyin": "wén",
            "tone": 2,
            "kangxi": 12,
            "simplified": 12,
            "wuxing": "水",
            "radical": "雨",
            "meaning": "有花纹的云彩",
            "gender_pref": "女",
            "style_tags": ["婉约"],
        },
        {
            "char": "煜",
            "pinyin": "yù",
            "tone": 4,
            "kangxi": 13,
            "simplified": 13,
            "wuxing": "火",
            "radical": "火",
            "meaning": "照耀光明",
            "gender_pref": "男",
            "style_tags": ["光明"],
        },
    ]

    with sqlite3.connect(":memory:") as conn:
        init_sqlite(conn)
        assert import_characters(conn, rows, data_source="test") == 2
        assert import_characters(conn, rows, data_source="test") == 2

        count = conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
        wen = conn.execute(
            "SELECT char, wuxing, gender_pref, data_source FROM characters WHERE char = '雯'"
        ).fetchone()

    assert count == 2
    assert wen == ("雯", "水", "女", "test")
