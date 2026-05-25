import json
import sqlite3
import zipfile

from scripts.import_characters import (
    import_characters,
    init_sqlite,
    normalize_character,
    parse_marked_pinyin,
    parse_unihan_zip,
)


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
    assert row["wuxing_source"] == "manual_review"
    assert row["wuxing_confidence"] == 90
    assert json.loads(row["style_tags"]) == ["婉约", "清丽"]
    assert json.loads(row["classics_refs"])


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


def test_parse_marked_pinyin_extracts_tone():
    assert parse_marked_pinyin("wén") == ("wén", 2)
    assert parse_marked_pinyin("zi") == ("zi", 5)


def test_parse_unihan_zip_reads_iicore_rows(tmp_path):
    zip_path = tmp_path / "Unihan.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "Unihan_IRGSources.txt",
            "\n".join([
                "U+4E00\tkIICore\tAGTJ",
                "U+4E00\tkTotalStrokes\t1",
                "U+4E00\tkRSUnicode\t1.0",
                "U+6C34\tkIICore\tAGTJ",
                "U+6C34\tkTotalStrokes\t4",
                "U+6C34\tkRSUnicode\t85.0",
            ]),
        )
        zf.writestr(
            "Unihan_Readings.txt",
            "\n".join([
                "U+4E00\tkMandarin\tyī",
                "U+6C34\tkMandarin\tshuǐ",
            ]),
        )

    rows = parse_unihan_zip(zip_path, limit=2)

    assert [row["char"] for row in rows] == ["一", "水"]
    assert rows[0]["tone"] == 1
    assert rows[1]["wuxing"] == "水"
    assert rows[1]["wuxing_confidence"] == 75
