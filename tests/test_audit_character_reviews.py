import csv
import sqlite3

from scripts.audit_character_reviews import fetch_unreviewed, write_review_csv
from scripts.import_characters import import_characters, init_sqlite


def test_fetch_unreviewed_skips_manual_reviewed_rows():
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
            "char": "一",
            "pinyin": "yī",
            "tone": 1,
            "kangxi": 1,
            "simplified": 1,
            "wuxing": "土",
            "wuxing_source": "unihan_iicore_default",
            "wuxing_confidence": 35,
            "meaning": "待校对",
            "gender_pref": "中性",
            "style_tags": ["待校对"],
        },
    ]
    with sqlite3.connect(":memory:") as conn:
        init_sqlite(conn)
        import_characters(conn, rows, data_source="test")

        unreviewed = fetch_unreviewed(conn, limit=10)

    assert [row["char"] for row in unreviewed] == ["一"]


def test_write_review_csv_adds_review_columns(tmp_path):
    output = tmp_path / "review.csv"
    write_review_csv([
        {
            "char": "一",
            "pinyin": "yī",
            "tone": 1,
            "kangxi_strokes": 1,
            "simplified_strokes": 1,
            "wuxing": "土",
            "wuxing_source": "unihan_iicore_default",
            "wuxing_confidence": 35,
            "radical": "1",
            "gender_pref": "中性",
            "meaning_primary": "待校对",
            "style_tags": "[\"待校对\"]",
        }
    ], output)

    with output.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows[0]["char"] == "一"
    assert "reviewed_wuxing" in rows[0]
    assert "review_note" in rows[0]
