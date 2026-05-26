from app.services.llm_review import _merge_reviews, build_review_messages


def _candidate(phonetic_score=57):
    return {
        "full_name": "张棠婷",
        "surname": "张",
        "given_chars": ["棠", "婷"],
        "total_score": 77.1,
        "scores": {
            "bazi": {"raw_score": 85, "breakdown": []},
            "wuge": {"raw_score": 79, "breakdown": []},
            "meaning": {"raw_score": 76, "breakdown": []},
            "phonetic": {
                "raw_score": phonetic_score,
                "breakdown": [
                    {"item": "声母", "delta": -8, "reason": "声母重复 ['z', 't', 't']"},
                    {"item": "韵母", "delta": -10, "reason": "韵母完全相同 ['ng', 'ng', 'ng']"},
                ],
            },
            "visual": {"raw_score": 81, "breakdown": []},
        },
        "wuge_result": {},
    }


def test_review_prompt_exposes_low_phonetic_breakdown():
    messages = build_review_messages(
        [_candidate()],
        {"bazi_string": "壬寅 癸丑 壬申 丙午", "day_master": "壬", "day_master_wuxing": "水"},
        {"primary": "火", "secondary": "火"},
    )

    assert "phonetic_breakdown" in messages["user"]
    assert "声母重复" in messages["user"]
    assert "音律读音分偏低" in messages["user"]
    assert "不要只写文化意境亮点" in messages["user"]


def test_merge_reviews_backfills_missing_phonetic_issue():
    merged = _merge_reviews(
        [_candidate()],
        [
            {
                "name": "张棠婷",
                "llm_score": 7.8,
                "highlight": "海棠婷立，温婉有致，文化意境统一",
                "issues": [],
            }
        ],
    )

    assert merged[0]["issues"]
    assert "音律读音分偏低" in merged[0]["issues"][0]
    assert "声母重复" in merged[0]["issues"][0]
