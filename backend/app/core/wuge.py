"""
三才五格计算模块

参考：熊崎健翁姓名学
笔画基准：康熙繁体笔画
计算公式：
    天格 = 姓笔画 + 1（单姓）
    人格 = 姓笔画 + 名第一字笔画
    地格 = 名第一字笔画 + 名第二字笔画（双名）
                  名第一字笔画 + 1（单名）
    外格 = 总格 − 人格 + 1
    总格 = 全部字笔画总和

三才 = 天/人/地三格个位数对应五行
    1,2=木  3,4=火  5,6=土  7,8=金  9,0=水
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal, Optional, List

# 引入 81 数理（用相对路径以避免循环导入）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "data" / "seed"))
from shuli_81 import get_shuli, MALE_TABOO, FEMALE_TABOO  # noqa: E402


WUXING_MAP = {
    1: "木", 2: "木",
    3: "火", 4: "火",
    5: "土", 6: "土",
    7: "金", 8: "金",
    9: "水", 0: "水",
}

# 五行相生：木→火→土→金→水→木
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相克：木→土→水→火→金→木
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def number_to_wuxing(n: int) -> str:
    """格数 → 五行（取个位数）"""
    return WUXING_MAP[n % 10]


def sancai_relation(heaven: str, person: str, earth: str) -> dict:
    """
    三才之间的相生相克关系判定
    返回 {天人关系, 人地关系, 总评}
    """
    def relate(a: str, b: str) -> str:
        if a == b:
            return "比和"
        if SHENG.get(a) == b:
            return "相生(顺)"
        if SHENG.get(b) == a:
            return "相生(逆)"
        if KE.get(a) == b:
            return "相克(克出)"
        if KE.get(b) == a:
            return "相克(被克)"
        return "无关"

    hp = relate(heaven, person)
    pe = relate(person, earth)

    # 综合评级
    bad_relations = {"相克(被克)", "相克(克出)"}
    if hp not in bad_relations and pe not in bad_relations:
        rating = "吉"
    elif hp in bad_relations and pe in bad_relations:
        rating = "凶"
    else:
        rating = "半吉"

    return {
        "heaven_person": hp,
        "person_earth": pe,
        "rating": rating,
    }


@dataclass
class WugeResult:
    """五格计算结果"""
    # 笔画
    surname_strokes: int
    name_strokes: List[int]

    # 五格
    tiange: int          # 天格
    renge: int           # 人格
    dige: int            # 地格
    waige: int           # 外格
    zongge: int          # 总格

    # 三才（五行）
    sancai_heaven: str
    sancai_person: str
    sancai_earth: str

    # 三才关系
    sancai_relation: dict

    # 五格吉凶
    tiange_info: dict
    renge_info: dict
    dige_info: dict
    waige_info: dict
    zongge_info: dict

    # 综合
    all_grids_lucky: bool      # 五格是否全吉
    has_taboo: bool             # 是否触犯男/女忌数
    taboo_details: List[str]    # 忌数说明

    def to_dict(self) -> dict:
        return asdict(self)


def compute_wuge(
    surname_strokes: int,
    name_strokes: List[int],
    gender: Literal["男", "女"] = "男",
) -> WugeResult:
    """
    核心计算函数

    Args:
        surname_strokes: 姓氏康熙笔画（单姓单值；复姓请先求和后传入）
        name_strokes: 名字各字康熙笔画的列表（1~2个元素）
        gender: 性别，影响忌数判定

    Returns:
        WugeResult 数据类
    """
    if len(name_strokes) not in (1, 2):
        raise ValueError(f"名字长度必须 1 或 2 字，收到 {len(name_strokes)} 字")

    # 1. 天格
    tiange = surname_strokes + 1

    # 2. 人格
    renge = surname_strokes + name_strokes[0]

    # 3. 地格
    if len(name_strokes) == 2:
        dige = name_strokes[0] + name_strokes[1]
    else:
        dige = name_strokes[0] + 1

    # 4. 总格
    zongge = surname_strokes + sum(name_strokes)

    # 5. 外格
    if len(name_strokes) == 2:
        waige = zongge - renge + 1
        # 等价: waige = name_strokes[1] + 1
    else:
        waige = 2  # 单名外格固定为 2（约定）

    # 三才
    sancai_h = number_to_wuxing(tiange)
    sancai_p = number_to_wuxing(renge)
    sancai_e = number_to_wuxing(dige)
    sancai_rel = sancai_relation(sancai_h, sancai_p, sancai_e)

    # 数理吉凶
    tiange_info = get_shuli(tiange)
    renge_info = get_shuli(renge)
    dige_info = get_shuli(dige)
    waige_info = get_shuli(waige)
    zongge_info = get_shuli(zongge)

    # 五格是否全吉（天格不计入，只看人/地/外/总）
    # 因为天格是姓决定，吉凶不由名字主导
    grids_to_check = [renge_info, dige_info, waige_info, zongge_info]
    all_lucky = all(g["level"] in ("大吉", "吉") for g in grids_to_check)

    # 忌数检查
    taboo_set = MALE_TABOO if gender == "男" else FEMALE_TABOO
    taboo_details = []
    for grid_name, grid_val in [
        ("人格", renge), ("地格", dige), ("外格", waige), ("总格", zongge),
    ]:
        if grid_val in taboo_set:
            taboo_details.append(f"{grid_name}={grid_val} 触犯{gender}命忌数")
    has_taboo = bool(taboo_details)

    return WugeResult(
        surname_strokes=surname_strokes,
        name_strokes=name_strokes,
        tiange=tiange,
        renge=renge,
        dige=dige,
        waige=waige,
        zongge=zongge,
        sancai_heaven=sancai_h,
        sancai_person=sancai_p,
        sancai_earth=sancai_e,
        sancai_relation=sancai_rel,
        tiange_info=tiange_info,
        renge_info=renge_info,
        dige_info=dige_info,
        waige_info=waige_info,
        zongge_info=zongge_info,
        all_grids_lucky=all_lucky,
        has_taboo=has_taboo,
        taboo_details=taboo_details,
    )


def generate_valid_combos(
    surname_strokes: int,
    min_stroke: int = 1,
    max_stroke: int = 24,
    fixed_strokes: Optional[dict] = None,
    gender: Literal["男", "女"] = "男",
) -> List[tuple]:
    """
    穷举所有"五格全吉 + 无忌数 + 三才不相克"的笔画组合。

    Args:
        surname_strokes: 姓氏康熙笔画
        min_stroke: 单字最小笔画
        max_stroke: 单字最大笔画
        fixed_strokes: 固定某位字的笔画 {"first": 13} 或 {"second": 12}
        gender: 性别（影响忌数）

    Returns:
        [(x, y), ...] 排序后的吉数组合
    """
    fixed_strokes = fixed_strokes or {}
    results = []

    for x in range(min_stroke, max_stroke + 1):
        if "first" in fixed_strokes and x != fixed_strokes["first"]:
            continue
        for y in range(min_stroke, max_stroke + 1):
            if "second" in fixed_strokes and y != fixed_strokes["second"]:
                continue

            res = compute_wuge(surname_strokes, [x, y], gender=gender)
            if res.all_grids_lucky and not res.has_taboo:
                # 排除三才大凶（被克）
                if res.sancai_relation["rating"] != "凶":
                    results.append((x, y))

    return results


if __name__ == "__main__":
    # 自测：张维城 (11-14-10) 应当全吉
    print("=== 测试 1：张维城 (11-14-10) ===")
    r = compute_wuge(11, [14, 10], gender="男")
    print(f"天{r.tiange} 人{r.renge} 地{r.dige} 外{r.waige} 总{r.zongge}")
    print(f"三才: {r.sancai_heaven}-{r.sancai_person}-{r.sancai_earth} "
          f"({r.sancai_relation['rating']})")
    print(f"五格全吉: {r.all_grids_lucky}, 忌数: {r.has_taboo}")
    print(f"详: 人格 {r.renge_info['meaning']}, 总格 {r.zongge_info['meaning']}")

    print("\n=== 测试 2：张昊轩 (11-8-10) 应当含人格19大凶 ===")
    r2 = compute_wuge(11, [8, 10], gender="男")
    print(f"人{r2.renge} ({r2.renge_info['level']} {r2.renge_info['meaning']})")
    print(f"忌数: {r2.has_taboo}, 详情: {r2.taboo_details}")

    print("\n=== 测试 3：张姓男孩 11-X-Y 全吉组合（X,Y 在 1-15）===")
    combos = generate_valid_combos(11, 1, 15, gender="男")
    print(f"找到 {len(combos)} 组：{combos[:10]}...")
