"""典籍 + 名人语料库测试"""
import pytest
from classics_corpus import CLASSICS_CORPUS, get_classics_for_char, get_books_summary
from famous_names_corpus import FAMOUS_NAMES, get_famous_for_char
from yijing_64 import GUA_64, get_gua, get_gua_by_hour


# ====== 典籍 ======

def test_classics_corpus_loaded():
    assert len(CLASSICS_CORPUS) >= 80


def test_classics_books_diversity():
    """覆盖至少 8 种典籍"""
    books = get_books_summary()
    assert len(books) >= 8
    # 必含主流经典
    for must_have in ["诗经", "楚辞", "论语", "唐诗", "宋词", "周易"]:
        assert must_have in books, f"缺少 {must_have}"


def test_get_classics_for_lan():
    """兰字应在楚辞中出现多次"""
    res = get_classics_for_char("兰")
    assert len(res) >= 2
    assert all(r["book"] == "楚辞" for r in res)


def test_get_classics_for_yue():
    """月字在唐诗中频次高"""
    res = get_classics_for_char("月")
    assert len(res) >= 3
    books = {r["book"] for r in res}
    assert "唐诗" in books


def test_no_classics_for_made_up_char():
    """不存在的字返回空"""
    res = get_classics_for_char("穒")
    assert res == []


# ====== 名人 ======

def test_famous_corpus_loaded():
    assert len(FAMOUS_NAMES) >= 50


def test_famous_li_bai_fame():
    """李白知名度应为顶级"""
    res = get_famous_for_char("白")
    assert any(f["full_name"] == "李白" and f["fame_score"] >= 95 for f in res)


def test_famous_returned_by_fame():
    """同字名人按 fame_score 倒序"""
    res = get_famous_for_char("明")
    if len(res) >= 2:
        for i in range(len(res) - 1):
            assert res[i]["fame_score"] >= res[i+1]["fame_score"]


def test_famous_for_wen():
    """雯字在现代名人中应能找到"""
    res = get_famous_for_char("雯")
    assert any("刘诗雯" == f["full_name"] for f in res)


# ====== 易经 64 卦 ======

def test_yijing_complete():
    assert len(GUA_64) == 64


def test_yijing_classic_gua():
    """乾/坤/泰/谦 等经典卦应能查到"""
    for name in ["乾", "坤", "泰", "谦", "晋", "鼎"]:
        g = get_gua(name)
        assert g is not None
        assert g["name"] == name


def test_yijing_hour_to_gua():
    """午时对应离卦"""
    assert get_gua_by_hour(12) == "离"
    assert get_gua_by_hour(0) == "坎"   # 子时
    assert get_gua_by_hour(6) == "震"   # 卯时
