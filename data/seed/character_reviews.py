"""
人工校对覆盖表。

合并两个来源（优先级从低到高）：
1. characters_seed.py 里 154 字的种子取名字段（视为已校对）。
2. reviewed_top1000.json 里 git 持久化的人工评审记录（Top1000 校对成果落地于此）。

导入流程的最后一步会用本表覆盖 Unihan 批量入库的低置信度字段，
保证人工劳动成果不被自动数据覆盖。
"""
from __future__ import annotations

import json
from pathlib import Path

from characters_seed import CHARACTERS_SEED

REVIEW_JSON_PATH = Path(__file__).resolve().parent / "reviewed_top1000.json"


def _load_seed_reviews() -> dict[str, dict]:
    # 种子 154 字属于 Claude 手工录入，视为"已校对"，
    # 标记为 manual_review 让 audit/导入流程认作高置信度。
    return {
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


def _load_json_reviews() -> dict[str, dict]:
    if not REVIEW_JSON_PATH.exists():
        return {}
    payload = json.loads(REVIEW_JSON_PATH.read_text(encoding="utf-8"))
    reviews = payload.get("reviews", []) if isinstance(payload, dict) else payload
    out: dict[str, dict] = {}
    for row in reviews:
        char = row["char"]
        reviewer = row.get("reviewer") or ""
        # auto_bootstrap 是机器引导，置信度中等；
        # 其它 reviewer 视为人工校对，置信度高。
        if reviewer.startswith("auto_bootstrap"):
            source = "auto_bootstrap"
            review_status = "auto"
            default_conf = 60
        else:
            source = "manual_review"
            review_status = "reviewed"
            default_conf = 95
        out[char] = {
            "wuxing": row["wuxing"],
            "wuxing_source": source,
            "wuxing_confidence": int(row.get("wuxing_confidence", default_conf)),
            "gender_pref": row.get("gender_pref", "中性"),
            "meaning": row["meaning"],
            "style_tags": row.get("style_tags", []),
            "classics_refs": row.get("classics_refs", []),
            "famous_refs": row.get("famous_refs", []),
            "review_status": review_status,
            "reviewer": reviewer,
            "reviewed_at": row.get("reviewed_at"),
        }
    return out


def _merge_reviews() -> dict[str, dict]:
    merged = _load_seed_reviews()
    merged.update(_load_json_reviews())
    return merged


REVIEWED_CHARACTERS: dict[str, dict] = _merge_reviews()


def get_reviewed_character(char: str) -> dict | None:
    return REVIEWED_CHARACTERS.get(char)


def reload() -> dict[str, dict]:
    """强制重新读取 JSON（用于校对脚本运行后立即看效果）。"""
    global REVIEWED_CHARACTERS
    REVIEWED_CHARACTERS = _merge_reviews()
    return REVIEWED_CHARACTERS
