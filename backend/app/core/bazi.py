"""
八字排盘模块

依赖：lunar-python（农历/公历转换、四柱排盘）
功能：
    - 公历/农历 → 四柱八字
    - 计算五行分布
    - 查询调候用神
    - 综合输出可解释的命理报告
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal, Optional

try:
    from lunar_python import Solar, Lunar
except ImportError:
    Solar = None
    Lunar = None

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "data" / "seed"))
from tiaohou_rules import get_tiaohou, TIANGAN_WUXING  # noqa: E402


# 地支五行
DIZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 地支藏干（地支中暗藏的天干）— 用于五行分布细化计算
DIZHI_CANG = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}


@dataclass
class BaziResult:
    """八字排盘结果"""
    # 输入
    input_datetime: str
    is_lunar: bool

    # 四柱
    year_gan: str
    year_zhi: str
    month_gan: str
    month_zhi: str
    day_gan: str         # 日主
    day_zhi: str
    hour_gan: str
    hour_zhi: str

    # 日主与月令
    day_master: str           # = day_gan
    day_master_wuxing: str
    birth_month_zhi: str      # = month_zhi
    month_name: str           # 农历月名

    # 五行分布
    wuxing_count: dict        # {"木": 2, "火": 1, "土": 2, "金": 0, "水": 3}
    wuxing_score: dict        # 含地支藏干的加权分

    # 调候用神
    tiaohou: dict             # get_tiaohou 返回值

    # 综合
    bazi_string: str          # "壬寅 癸丑 甲戌 庚午"

    def to_dict(self) -> dict:
        return asdict(self)


def _check_lunar_lib():
    if Solar is None:
        raise ImportError(
            "lunar-python 未安装。请运行: pip install lunar-python"
        )


def compute_bazi(
    year: int, month: int, day: int, hour: int, minute: int = 0,
    is_lunar: bool = False,
    gender: Literal["男", "女"] = "男",
) -> BaziResult:
    """
    主排盘函数

    Args:
        year, month, day, hour, minute: 公历或农历日期时间
        is_lunar: True=农历, False=公历
        gender: 性别（影响某些大运推算，本函数暂不计算大运）

    Returns:
        BaziResult
    """
    _check_lunar_lib()

    # 1. 农历/公历 → Solar 对象
    if is_lunar:
        lunar = Lunar.fromYmdHms(year, month, day, hour, minute, 0)
        solar = lunar.getSolar()
    else:
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()

    # 2. 取八字（注意：lunar-python 内部已处理立春节气分界）
    ba = lunar.getEightChar()

    year_gz = ba.getYear()      # "壬寅"
    month_gz = ba.getMonth()    # "癸丑"
    day_gz = ba.getDay()        # "甲戌"
    hour_gz = ba.getTime()      # "庚午"

    year_gan, year_zhi = year_gz[0], year_gz[1]
    month_gan, month_zhi = month_gz[0], month_gz[1]
    day_gan, day_zhi = day_gz[0], day_gz[1]
    hour_gan, hour_zhi = hour_gz[0], hour_gz[1]

    # 3. 五行简单计数（只数天干+地支本气）
    wuxing_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for g in [year_gan, month_gan, day_gan, hour_gan]:
        wuxing_count[TIANGAN_WUXING[g]] += 1
    for z in [year_zhi, month_zhi, day_zhi, hour_zhi]:
        wuxing_count[DIZHI_WUXING[z]] += 1

    # 4. 五行加权打分（含地支藏干，主气1.0/中气0.6/余气0.3）
    weights = [1.0, 0.6, 0.3]
    wuxing_score = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    for g in [year_gan, month_gan, day_gan, hour_gan]:
        wuxing_score[TIANGAN_WUXING[g]] += 1.0
    for z in [year_zhi, month_zhi, day_zhi, hour_zhi]:
        cangs = DIZHI_CANG[z]
        for i, c in enumerate(cangs):
            w = weights[i] if i < len(weights) else 0.1
            wuxing_score[TIANGAN_WUXING[c]] += w

    # 四舍五入
    for k in wuxing_score:
        wuxing_score[k] = round(wuxing_score[k], 2)

    # 5. 调候用神
    tiaohou = get_tiaohou(day_gan, month_zhi)

    # 6. 月份中文名
    month_names = ["正", "二", "三", "四", "五", "六",
                   "七", "八", "九", "十", "冬", "腊"]
    month_name = f"{month_names[lunar.getMonth()-1]}月"

    return BaziResult(
        input_datetime=f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        is_lunar=is_lunar,
        year_gan=year_gan, year_zhi=year_zhi,
        month_gan=month_gan, month_zhi=month_zhi,
        day_gan=day_gan, day_zhi=day_zhi,
        hour_gan=hour_gan, hour_zhi=hour_zhi,
        day_master=day_gan,
        day_master_wuxing=TIANGAN_WUXING[day_gan],
        birth_month_zhi=month_zhi,
        month_name=month_name,
        wuxing_count=wuxing_count,
        wuxing_score=wuxing_score,
        tiaohou=tiaohou,
        bazi_string=f"{year_gz} {month_gz} {day_gz} {hour_gz}",
    )


def get_naming_wuxing(bazi: BaziResult) -> dict:
    """
    从八字结果中导出取名应该补的五行。

    返回：
        {
            "primary": "火",       # 首选补益五行
            "secondary": "土",     # 次选补益五行
            "avoid": ["水"],       # 应避免的五行
            "reasoning": "..."     # 理由
        }
    """
    th = bazi.tiaohou
    return {
        "primary": th["primary_wuxing"],
        "secondary": th["secondary_wuxing"],
        "avoid": [th["avoid_wuxing"]] if th["avoid_wuxing"] else [],
        "reasoning": (
            f"{bazi.day_master}日主生于{bazi.birth_month_zhi}月（{bazi.month_name}），"
            f"调候用神为「{th['primary_yongshen']}」({th['primary_wuxing']})，"
            f"辅以「{th['secondary_yongshen']}」({th['secondary_wuxing']})。"
            f"{th['explanation']}"
        )
    }


if __name__ == "__main__":
    print("=" * 60)
    print("八字排盘测试")
    print("=" * 60)

    # 案例 1：本项目宝宝（男）— 2023-01-14 11:33 公历
    print("\n【案例 1】宝宝男 公历 2023-01-14 11:33")
    print("权威八字：壬寅 癸丑 壬申 丙午（壬水冬生）")
    print("-" * 60)
    r = compute_bazi(2023, 1, 14, 11, 33, is_lunar=False, gender="男")
    print(f"八字：{r.bazi_string}")
    print(f"日主：{r.day_master}({r.day_master_wuxing})")
    print(f"月令：{r.birth_month_zhi}月（{r.month_name}）")
    print(f"五行统计：{r.wuxing_count}")
    print(f"五行加权：{r.wuxing_score}")
    print(f"调候用神：")
    print(f"  主：{r.tiaohou['primary_yongshen']}({r.tiaohou['primary_wuxing']})")
    print(f"  次：{r.tiaohou['secondary_yongshen']}({r.tiaohou['secondary_wuxing']})")
    print(f"  忌：{r.tiaohou['avoid_wuxing']}")
    print(f"  解：{r.tiaohou['explanation']}")
    naming = get_naming_wuxing(r)
    print(f"\n取名应补：{naming['primary']} / {naming['secondary']}，避：{naming['avoid']}")

    # 案例 2：爸爸 农历 1992-12-29 寅时
    print("\n【案例 2】爸爸 农历 1992-12-29 寅时（约4:30）")
    print("-" * 60)
    r2 = compute_bazi(1992, 12, 29, 4, 30, is_lunar=True, gender="男")
    print(f"八字：{r2.bazi_string}")
    print(f"日主：{r2.day_master}({r2.day_master_wuxing})")
    print(f"调候用神：{r2.tiaohou['primary_yongshen']}({r2.tiaohou['primary_wuxing']})"
          f" + {r2.tiaohou['secondary_yongshen']}({r2.tiaohou['secondary_wuxing']})")

    # 案例 3：妈妈 农历 1993-09-22 下午 3:45
    print("\n【案例 3】妈妈 农历 1993-09-22 15:45")
    print("-" * 60)
    r3 = compute_bazi(1993, 9, 22, 15, 45, is_lunar=True, gender="女")
    print(f"八字：{r3.bazi_string}")
    print(f"日主：{r3.day_master}({r3.day_master_wuxing})")
    print(f"调候用神：{r3.tiaohou['primary_yongshen']}({r3.tiaohou['primary_wuxing']})"
          f" + {r3.tiaohou['secondary_yongshen']}({r3.tiaohou['secondary_wuxing']})")
