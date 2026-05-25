"""评分引擎单元测试"""
import pytest
from app.core.scoring import score_name


WX_FIRE = {
    "primary": "火",
    "secondary": "火",
    "avoid": ["水"],
    "reasoning": "test"
}


def test_score_zhang_dun_xiang_high():
    """张敦翔 应得高分（敦=火主用神，五格全吉）"""
    s = score_name("张", ["敦", "翔"], WX_FIRE, gender="男")
    assert s.total_score > 75
    assert s.bazi.raw_score > 80   # 用神补到
    assert s.wuge.raw_score > 80   # 五格全吉


def test_score_zhang_hao_xuan_penalized():
    """张昊轩 因人格19大凶 应低于敦翔"""
    s = score_name("张", ["昊", "轩"], WX_FIRE, gender="男")
    # 五格被忌数严重扣分
    assert s.wuge.raw_score < 50


def test_bazi_avoid_penalty():
    """名字字命中忌神应被扣分"""
    wx_avoid_water = {"primary": "火", "secondary": "土",
                       "avoid": ["水"], "reasoning": "test"}
    # 张涵雯 两个水字（忌神）
    s = score_name("张", ["涵", "雯"], wx_avoid_water, gender="女")
    assert s.bazi.raw_score < 60   # 双忌神，应严重扣分


def test_meaning_classics_bonus():
    """字带典籍出处应在字义维度加分"""
    # 维城 出自《诗经》"宗子维城"
    s = score_name("张", ["维", "城"], WX_FIRE, gender="男")
    assert s.meaning.raw_score > 55  # 典籍加分体现


def test_custom_weights_change_weighted_total():
    default = score_name("张", ["维", "城"], WX_FIRE, gender="男")
    custom = score_name(
        "张", ["维", "城"], WX_FIRE, gender="男",
        weights={"bazi": 1, "wuge": 0, "meaning": 0, "phonetic": 0, "visual": 0},
    )

    assert custom.total_score == custom.bazi.raw_score
    assert custom.total_score != default.total_score


def test_compound_surname_can_be_scored():
    s = score_name("欧阳", ["维", "城"], WX_FIRE, gender="男")

    assert s.full_name == "欧阳维城"
    assert s.wuge_result["surname_strokes"] == 32
    assert 0 <= s.total_score <= 100
