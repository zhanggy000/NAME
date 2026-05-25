"""
名字生成主管线

按 REQUIREMENTS.md 第六甲节规定的「严格执行的取名顺序」：
    1. 八字排盘    →  孩子是谁
    2. 定用神      →  需要补什么
    3. 选五行      →  字库筛选范围
    4. 笔画穷举    →  五格全吉的组合
    5. 字义筛选    →  典籍出处 + 名人参照
    6. 音形复审    →  谐音、字形、性别气质
    7. LLM 终审    →  时代感、整体韵味（后续模块）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "data" / "seed"))
sys.path.insert(0, str(_ROOT / "backend"))

from characters_seed import CHARACTERS_SEED, get_char, find_chars  # noqa: E402
from app.core.bazi import compute_bazi, get_naming_wuxing  # noqa: E402
from app.core.wuge import compute_wuge  # noqa: E402
from app.core.scoring import score_name, NameScore  # noqa: E402


@dataclass
class GenerateRequest:
    """生成请求"""
    surname: str
    gender: Literal["男", "女"]
    # 八字
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    is_lunar: bool = False
    # 偏好
    must_include: Optional[str] = None             # 必含字，如 "雯"
    must_include_position: Optional[Literal["first", "second", "any"]] = "any"
    must_avoid: Optional[list[str]] = None         # 必避字
    style_prefs: Optional[list[str]] = None        # 风格 ["典雅","大气"]
    name_length: int = 2                            # 名字字数（不含姓）
    top_n: int = 10                                 # 返回前 N 个


def _filter_chars_by_wuxing_pool(
    target_wuxings: list[str],
    gender: str,
    style_prefs: Optional[list[str]] = None,
    exclude: Optional[set[str]] = None,
) -> list[dict]:
    """按用神五行池+性别+风格筛选字"""
    exclude = exclude or set()
    pool = []
    seen = set()
    for wx in target_wuxings:
        if not wx:
            continue
        for ch in find_chars(wuxing=wx, gender=gender, style_tags=style_prefs):
            if ch["char"] in seen or ch["char"] in exclude:
                continue
            # 排除姓氏字（避免名字含姓氏字）
            if not ch.get("style_tags") and ch["meaning"].startswith("姓氏"):
                continue
            seen.add(ch["char"])
            pool.append(ch)
    return pool


def generate_names(req: GenerateRequest) -> dict:
    """
    主生成函数。

    返回：
        {
            "bazi": {...},
            "naming_wuxing": {...},
            "candidates": [NameScore.to_dict(), ...],
            "stats": {"considered": N, "returned": M}
        }
    """
    # === 步骤 1-2：排八字 + 定用神 ===
    bazi = compute_bazi(
        req.year, req.month, req.day, req.hour, req.minute,
        is_lunar=req.is_lunar, gender=req.gender,
    )
    naming_wuxing = get_naming_wuxing(bazi)

    # === 步骤 3：选五行 ===
    target_wuxings = [naming_wuxing["primary"], naming_wuxing["secondary"]]
    avoid_wuxings = naming_wuxing.get("avoid", [])

    # === 必含字处理 ===
    must_char_info = None
    if req.must_include:
        must_char_info = get_char(req.must_include)
        if not must_char_info:
            raise ValueError(f"必含字「{req.must_include}」不在字库中")

    # === 步骤 4：笔画穷举 + 五行字筛选 ===
    surname_info = get_char(req.surname)
    if not surname_info:
        raise ValueError(f"姓氏「{req.surname}」不在字库中")
    sn_strokes = surname_info["kangxi"]

    # 候选字池（按用神五行筛）
    avoid_set = set(req.must_avoid or [])
    if req.must_include:
        avoid_set.add(req.must_include)  # 已经固定不重复加
    pool = _filter_chars_by_wuxing_pool(
        target_wuxings, req.gender, req.style_prefs,
        exclude=avoid_set,
    )

    # 如果用神字数不足，放宽到不在 avoid 的所有字
    if len(pool) < 5:
        pool = [c for c in CHARACTERS_SEED
                if c.get("style_tags")  # 非姓氏字
                and c["wuxing"] not in avoid_wuxings
                and c["char"] not in avoid_set
                and (c["gender_pref"] in (req.gender, "中性"))]

    # === 构造候选名字（笛卡尔积，考虑必含字位置）===
    candidates = []  # 列表存 (char_list, NameScore)
    considered = 0

    if req.name_length == 2:
        # 双字名
        positions_to_fill = []
        if req.must_include:
            if req.must_include_position == "first":
                positions_to_fill = [("fixed_first", must_char_info)]
            elif req.must_include_position == "second":
                positions_to_fill = [("fixed_second", must_char_info)]
            else:
                positions_to_fill = [
                    ("fixed_first", must_char_info),
                    ("fixed_second", must_char_info),
                ]
        else:
            positions_to_fill = [("free", None)]

        for mode, fixed in positions_to_fill:
            for c1 in pool:
                for c2 in pool:
                    if c1["char"] == c2["char"]:
                        continue
                    if mode == "fixed_first":
                        chars = [fixed, c2]
                        if c2["char"] == fixed["char"]:
                            continue
                    elif mode == "fixed_second":
                        chars = [c1, fixed]
                        if c1["char"] == fixed["char"]:
                            continue
                    else:
                        chars = [c1, c2]

                    # 快速过滤：硬要求是「人格+总格不为大凶 + 三才不为凶」
                    # 不硬性使用全部 41 个凶数 + 忌数，避免过度过滤
                    # （女命首领数 21/23/33 这类争议数交给评分层降分而非拒收）
                    wuge = compute_wuge(
                        sn_strokes,
                        [chars[0]["kangxi"], chars[1]["kangxi"]],
                        gender=req.gender,
                    )
                    considered += 1
                    # 硬过滤：人格/总格不能为大凶
                    if wuge.renge_info["level"] == "大凶":
                        continue
                    if wuge.zongge_info["level"] == "大凶":
                        continue
                    if wuge.dige_info["level"] == "大凶":
                        continue
                    if wuge.sancai_relation["rating"] == "凶":
                        continue

                    # 五格通过 → 完整评分
                    try:
                        ns = score_name(
                            req.surname,
                            [chars[0]["char"], chars[1]["char"]],
                            naming_wuxing, gender=req.gender,
                            style_prefs=req.style_prefs,
                        )
                        candidates.append(ns)
                    except ValueError:
                        continue

                # 单遍 fixed_first 不需要外层 c2 循环
                if mode == "fixed_first":
                    break
            if mode == "fixed_second":
                pass  # 内层 c1 已遍历
    else:
        raise NotImplementedError("当前仅支持双字名")

    # === 步骤 5-7（部分）：排序去重 ===
    seen_names = set()
    unique_candidates = []
    for ns in sorted(candidates, key=lambda x: x.total_score, reverse=True):
        if ns.full_name in seen_names:
            continue
        seen_names.add(ns.full_name)
        unique_candidates.append(ns)

    top = unique_candidates[: req.top_n]

    return {
        "bazi": bazi.to_dict(),
        "naming_wuxing": naming_wuxing,
        "candidates": [ns.to_dict() for ns in top],
        "stats": {
            "pool_size": len(pool),
            "considered": considered,
            "valid_wuge": len(candidates),
            "unique": len(unique_candidates),
            "returned": len(top),
        },
    }


def _print_result(title: str, result: dict):
    bz = result["bazi"]
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    print(f"八字：{bz['bazi_string']}")
    print(f"日主：{bz['day_master']}({bz['day_master_wuxing']}) "
          f"生于 {bz['birth_month_zhi']}月（{bz['month_name']}）")
    nw = result["naming_wuxing"]
    print(f"用神：{nw['primary']} / {nw['secondary']}，避：{nw['avoid']}")
    s = result["stats"]
    print(f"枚举 {s['considered']} 组 → 五格通过 {s['valid_wuge']} → 返回 {s['returned']}")
    print(f"\n{'排名':<6}{'名字':<10}{'总分':<10}{'八字':<8}{'五格':<8}{'字义':<8}")
    print("-" * 60)
    for i, c in enumerate(result["candidates"], 1):
        ss = c["scores"]
        print(f"{i:<6}{c['full_name']:<8}{c['total_score']:<10}"
              f"{ss['bazi']['raw_score']:<8}"
              f"{ss['wuge']['raw_score']:<8}"
              f"{ss['meaning']['raw_score']:<8}")


if __name__ == "__main__":
    # 测试 1：本项目宝宝男（壬水冬生）
    req = GenerateRequest(
        surname="张",
        gender="男",
        year=2023, month=1, day=14, hour=11, minute=33,
        is_lunar=False,
        name_length=2,
        top_n=10,
    )

    result1 = generate_names(req)
    _print_result("【场景 1】男宝 张姓 2023-01-14 11:33（壬水丑月用神火）", result1)

    # 测试 2：女宝必含 "雯" 字
    req2 = GenerateRequest(
        surname="张",
        gender="女",
        year=2026, month=5, day=25, hour=14, minute=30,
        is_lunar=False,
        must_include="雯",
        must_include_position="second",
        name_length=2,
        top_n=10,
    )
    result2 = generate_names(req2)
    _print_result("【场景 2】女宝 张姓 末字必含「雯」", result2)
