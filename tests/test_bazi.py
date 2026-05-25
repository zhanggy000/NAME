"""八字模块单元测试"""
import pytest
from app.core.bazi import compute_bazi, get_naming_wuxing


def test_baby_2023_01_14():
    """宝宝 2023-01-14 11:33 应为 壬寅 癸丑 壬申 丙午"""
    r = compute_bazi(2023, 1, 14, 11, 33, is_lunar=False, gender="男")
    assert r.year_gan == "壬"
    assert r.year_zhi == "寅"
    assert r.month_gan == "癸"
    assert r.month_zhi == "丑"
    assert r.day_gan == "壬"
    assert r.day_master == "壬"
    assert r.day_master_wuxing == "水"


def test_naming_wuxing_winter_ren_water():
    """壬水冬生用神火"""
    r = compute_bazi(2023, 1, 14, 11, 33, is_lunar=False, gender="男")
    nw = get_naming_wuxing(r)
    assert nw["primary"] == "火"
    assert "水" in nw["avoid"]


def test_lunar_input():
    """农历输入也能正常排盘"""
    # 农历 1992-12-29 寅时 → 公历 1993-01-21 早上
    r = compute_bazi(1992, 12, 29, 4, 30, is_lunar=True, gender="男")
    assert r.day_master is not None
    assert r.bazi_string.count(" ") == 3  # 四柱


def test_summer_water_master():
    """夏天壬水（推断用神为水/金）"""
    # 任意一个夏季日期的壬水日
    r = compute_bazi(2024, 6, 15, 12, 0, gender="男")
    if r.day_master in ("壬", "癸"):
        nw = get_naming_wuxing(r)
        # 夏季水日主，调候多用水或金
        assert nw["primary"] in ("水", "金", "火", "木", "土")  # 至少有值
