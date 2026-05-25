"""五格计算单元测试"""
import pytest
from app.core.wuge import (
    compute_wuge, number_to_wuxing, sancai_relation,
    generate_valid_combos,
)


def test_number_to_wuxing():
    """格数 → 五行"""
    assert number_to_wuxing(11) == "木"
    assert number_to_wuxing(12) == "木"
    assert number_to_wuxing(13) == "火"
    assert number_to_wuxing(24) == "火"
    assert number_to_wuxing(25) == "土"
    assert number_to_wuxing(17) == "金"
    assert number_to_wuxing(19) == "水"
    assert number_to_wuxing(20) == "水"


def test_zhang_wei_cheng():
    """张维城 (11-14-10) 五格全吉"""
    r = compute_wuge(11, [14, 10], gender="男")
    assert r.tiange == 12
    assert r.renge == 25
    assert r.dige == 24
    assert r.waige == 11
    assert r.zongge == 35
    assert r.renge_info["level"] == "大吉"
    assert r.zongge_info["level"] == "大吉"
    assert r.all_grids_lucky
    assert not r.has_taboo


def test_zhang_hao_xuan_should_have_taboo():
    """张昊轩 (11-8-10) 人格19 是男命大凶忌数"""
    r = compute_wuge(11, [8, 10], gender="男")
    assert r.renge == 19
    assert r.renge_info["level"] == "大凶"
    assert r.has_taboo
    assert any("人格" in d for d in r.taboo_details)


def test_zhang_dun_xiang():
    """张敦翔 (11-12-12) 双 12 画全吉"""
    r = compute_wuge(11, [12, 12], gender="男")
    assert r.renge == 23
    assert r.dige == 24
    assert r.waige == 13
    assert r.zongge == 35
    assert r.all_grids_lucky


def test_single_name():
    """单字名外格固定为 2"""
    r = compute_wuge(11, [12], gender="男")
    assert r.waige == 2
    assert r.zongge == 23


def test_sancai_relation_sheng():
    """三才相生顺畅"""
    rel = sancai_relation("木", "火", "土")
    assert rel["heaven_person"] == "相生(顺)"
    assert rel["person_earth"] == "相生(顺)"
    assert rel["rating"] == "吉"


def test_sancai_relation_ke():
    """三才相克为凶"""
    rel = sancai_relation("金", "木", "土")
    assert rel["rating"] in ("半吉", "凶")


def test_generate_valid_combos_smoke():
    """穷举姓张笔画 1-15 应能找到组合"""
    combos = generate_valid_combos(11, 1, 15, gender="男")
    assert len(combos) > 0
    # 张敦翔 应在内
    assert (12, 12) in combos
    # 张维城 应在内
    assert (14, 10) in combos


def test_generate_with_fixed_strokes():
    """固定末字笔画"""
    combos = generate_valid_combos(11, 1, 20, fixed_strokes={"second": 12}, gender="女")
    # 所有组合的第二位应都是 12
    for x, y in combos:
        assert y == 12
