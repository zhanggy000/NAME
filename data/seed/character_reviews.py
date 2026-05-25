"""
人工校对覆盖表。

这里存放已经人工确认过的取名关键字段。导入外部大字库后，应最后应用本覆盖表，
避免低置信度的批量数据覆盖高质量取名字段。
"""
from __future__ import annotations

from characters_seed import CHARACTERS_SEED


REVIEWED_CHARACTERS = {
    row["char"]: {
        "wuxing": row["wuxing"],
        "wuxing_source": "manual_review",
        "wuxing_confidence": 90,
        "gender_pref": row.get("gender_pref", "中性"),
        "meaning": row["meaning"],
        "style_tags": row.get("style_tags", []),
        "classics_refs": row.get("classics_refs", []),
        "famous_refs": row.get("famous_refs", []),
        "review_status": "reviewed",
    }
    for row in CHARACTERS_SEED
}


def get_reviewed_character(char: str) -> dict | None:
    return REVIEWED_CHARACTERS.get(char)
