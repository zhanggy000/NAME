"""
五维评分引擎

按 REQUIREMENTS.md 的核心理念实现：
    八字补益 30%（八字是灵魂，不可让五格凌驾）
    三才五格 25%
    字义寓意 20%
    音律读音 15%
    字形书写 10%

每个评分函数返回 (score, breakdown_list)，便于解释。
breakdown_list 是 [{"item": "...", "delta": ±X, "reason": "..."}] 形式。
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "data" / "seed"))
sys.path.insert(0, str(_ROOT / "backend"))

from characters_seed import get_char  # noqa: E402
from app.core.wuge import compute_wuge, WugeResult  # noqa: E402


# ============================================================
# 默认权重（可被用户覆盖）
# ============================================================
DEFAULT_WEIGHTS = {
    "bazi":    0.30,
    "wuge":    0.25,
    "meaning": 0.20,
    "phonetic": 0.15,
    "visual":  0.10,
}


@dataclass
class DimensionScore:
    """单维度评分结果"""
    name: str
    raw_score: float       # 0~100
    weighted_score: float  # raw × weight
    breakdown: list        # [{"item":"","delta":±X,"reason":""}]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NameScore:
    """名字完整评分"""
    full_name: str
    surname: str
    given_chars: list[str]

    bazi:    DimensionScore
    wuge:    DimensionScore
    meaning: DimensionScore
    phonetic: DimensionScore
    visual:  DimensionScore

    total_score: float  # 0~100
    wuge_result: dict   # 五格详情（用于前端展示）

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "surname": self.surname,
            "given_chars": self.given_chars,
            "scores": {
                "bazi": self.bazi.to_dict(),
                "wuge": self.wuge.to_dict(),
                "meaning": self.meaning.to_dict(),
                "phonetic": self.phonetic.to_dict(),
                "visual": self.visual.to_dict(),
            },
            "total_score": self.total_score,
            "wuge_result": self.wuge_result,
        }


# ============================================================
# ① 八字补益评分（0-100，权重 30%）
# ============================================================
def score_bazi(
    chars: list[dict],
    naming_wuxing: dict,
) -> DimensionScore:
    """
    评估名字字的五行是否符合八字用神。

    naming_wuxing = {
        "primary": "火",
        "secondary": "土",
        "avoid": ["水"],
        "reasoning": "..."
    }
    """
    breakdown = []
    score = 60.0  # 基础分

    primary = naming_wuxing.get("primary")
    secondary = naming_wuxing.get("secondary")
    avoid = naming_wuxing.get("avoid", [])

    # 每个字的五行评分
    for i, ch in enumerate(chars):
        pos = f"第{i+1}字「{ch['char']}」"
        wx = ch["wuxing"]

        if wx == primary:
            score += 18
            breakdown.append({
                "item": pos, "delta": +18,
                "reason": f"{wx}行 = 主用神 ✓"
            })
        elif wx == secondary:
            score += 12
            breakdown.append({
                "item": pos, "delta": +12,
                "reason": f"{wx}行 = 次用神 ✓"
            })
        elif wx in avoid:
            score -= 20
            breakdown.append({
                "item": pos, "delta": -20,
                "reason": f"{wx}行 = 忌神 ✗"
            })
        else:
            score += 3
            breakdown.append({
                "item": pos, "delta": +3,
                "reason": f"{wx}行 = 中性"
            })

    # 双字组合加分：若两字均补用神
    char_wx = [c["wuxing"] for c in chars]
    if all(w == primary for w in char_wx):
        score += 5
        breakdown.append({
            "item": "整体", "delta": +5,
            "reason": "双字均补主用神，调候力度极强"
        })
    elif primary in char_wx and secondary in char_wx:
        score += 4
        breakdown.append({
            "item": "整体", "delta": +4,
            "reason": "主用神+次用神并存，五行兼顾"
        })

    raw = max(0.0, min(100.0, score))
    return DimensionScore(
        name="八字补益",
        raw_score=round(raw, 1),
        weighted_score=round(raw * DEFAULT_WEIGHTS["bazi"], 2),
        breakdown=breakdown,
    )


# ============================================================
# ② 三才五格评分（0-100，权重 25%）
# ============================================================
def score_wuge_sancai(wuge: WugeResult, gender: str = "男") -> DimensionScore:
    breakdown = []
    score = 30.0  # 基础分

    # 人格（最关键）
    rl = wuge.renge_info["level"]
    if rl == "大吉":
        score += 22; breakdown.append({"item": f"人格{wuge.renge}", "delta": +22, "reason": f"大吉「{wuge.renge_info['meaning']}」"})
    elif rl == "吉":
        score += 16; breakdown.append({"item": f"人格{wuge.renge}", "delta": +16, "reason": f"吉「{wuge.renge_info['meaning']}」"})
    elif rl == "半吉":
        score += 6;  breakdown.append({"item": f"人格{wuge.renge}", "delta": +6,  "reason": f"半吉「{wuge.renge_info['meaning']}」"})
    elif rl == "凶":
        score -= 15; breakdown.append({"item": f"人格{wuge.renge}", "delta": -15, "reason": f"凶「{wuge.renge_info['meaning']}」"})
    else:  # 大凶
        score -= 25; breakdown.append({"item": f"人格{wuge.renge}", "delta": -25, "reason": f"大凶「{wuge.renge_info['meaning']}」"})

    # 总格
    zl = wuge.zongge_info["level"]
    if zl == "大吉":
        score += 18; breakdown.append({"item": f"总格{wuge.zongge}", "delta": +18, "reason": f"大吉「{wuge.zongge_info['meaning']}」"})
    elif zl == "吉":
        score += 12; breakdown.append({"item": f"总格{wuge.zongge}", "delta": +12, "reason": f"吉「{wuge.zongge_info['meaning']}」"})
    elif zl == "半吉":
        score += 4
    elif zl == "凶":
        score -= 12; breakdown.append({"item": f"总格{wuge.zongge}", "delta": -12, "reason": f"凶「{wuge.zongge_info['meaning']}」"})
    else:
        score -= 20; breakdown.append({"item": f"总格{wuge.zongge}", "delta": -20, "reason": f"大凶「{wuge.zongge_info['meaning']}」"})

    # 地格
    dl = wuge.dige_info["level"]
    if dl in ("大吉", "吉"):
        score += 10; breakdown.append({"item": f"地格{wuge.dige}", "delta": +10, "reason": f"{dl}「{wuge.dige_info['meaning']}」"})
    elif dl == "凶":
        score -= 8
    elif dl == "大凶":
        score -= 14; breakdown.append({"item": f"地格{wuge.dige}", "delta": -14, "reason": f"大凶「{wuge.dige_info['meaning']}」"})

    # 外格
    wl = wuge.waige_info["level"]
    if wl in ("大吉", "吉"):
        score += 6; breakdown.append({"item": f"外格{wuge.waige}", "delta": +6, "reason": f"{wl}"})
    elif wl == "大凶":
        score -= 8

    # 忌数惩罚
    if wuge.has_taboo:
        score -= 15
        breakdown.append({"item": "忌数", "delta": -15, "reason": "; ".join(wuge.taboo_details)})

    # 三才关系
    rating = wuge.sancai_relation["rating"]
    if rating == "吉":
        score += 8
        breakdown.append({"item": f"三才{wuge.sancai_heaven}-{wuge.sancai_person}-{wuge.sancai_earth}", "delta": +8, "reason": "相生顺畅"})
    elif rating == "半吉":
        score += 2
    else:
        score -= 5
        breakdown.append({"item": f"三才{wuge.sancai_heaven}-{wuge.sancai_person}-{wuge.sancai_earth}", "delta": -5, "reason": "相克不顺"})

    raw = max(0.0, min(100.0, score))
    return DimensionScore(
        name="三才五格",
        raw_score=round(raw, 1),
        weighted_score=round(raw * DEFAULT_WEIGHTS["wuge"], 2),
        breakdown=breakdown,
    )


# ============================================================
# ③ 字义寓意评分（0-100，权重 20%）
# ============================================================
def score_meaning(chars: list[dict], style_prefs: Optional[list[str]] = None) -> DimensionScore:
    breakdown = []
    score = 50.0  # 基础分

    for i, ch in enumerate(chars):
        pos = f"第{i+1}字「{ch['char']}」"
        # 典籍出处加分
        classics = ch.get("classics_refs") or []
        if classics:
            bonus = min(len(classics) * 6, 15)
            score += bonus
            breakdown.append({
                "item": pos, "delta": +bonus,
                "reason": f"典籍出处：{classics[0]}" + (f" 等 {len(classics)} 条" if len(classics) > 1 else "")
            })

        # 名人加分
        famous = ch.get("famous_refs") or []
        if famous:
            bonus = min(len(famous) * 3, 8)
            score += bonus
            breakdown.append({
                "item": pos, "delta": +bonus,
                "reason": f"名人参照：{famous[0]}" + (f" 等 {len(famous)} 位" if len(famous) > 1 else "")
            })

        # 风格匹配加分
        if style_prefs:
            tags = ch.get("style_tags", [])
            matches = set(tags) & set(style_prefs)
            if matches:
                score += len(matches) * 2
                breakdown.append({
                    "item": pos, "delta": +len(matches)*2,
                    "reason": f"风格匹配：{','.join(matches)}"
                })

    raw = max(0.0, min(100.0, score))
    return DimensionScore(
        name="字义寓意",
        raw_score=round(raw, 1),
        weighted_score=round(raw * DEFAULT_WEIGHTS["meaning"], 2),
        breakdown=breakdown,
    )


# ============================================================
# ④ 音律读音评分（0-100，权重 15%）
# ============================================================
def score_phonetic(surname_info: dict, chars: list[dict]) -> DimensionScore:
    breakdown = []
    score = 70.0  # 基础分

    all_chars = [surname_info] + chars
    tones = [c["tone"] for c in all_chars]
    pinyins = [c["pinyin"] for c in all_chars]

    # 1. 声调多样性
    if len(set(tones)) == 1:
        score -= 15
        breakdown.append({"item": "声调", "delta": -15, "reason": f"三字同调 {tones}，单调"})
    elif len(set(tones)) == len(tones):
        score += 12
        breakdown.append({"item": "声调", "delta": +12, "reason": f"声调多样 {tones}，富有变化"})
    else:
        score += 5
        breakdown.append({"item": "声调", "delta": +5, "reason": f"声调 {tones}，有变化"})

    # 2. 三连仄声扣分
    if all(t in (3, 4) for t in tones):
        score -= 8
        breakdown.append({"item": "声调", "delta": -8, "reason": "三连仄声，发音偏硬"})

    # 3. 声母重复检查（取拼音首字母）
    initials = [p[0] for p in pinyins]
    if len(set(initials)) < len(initials):
        # 有重复
        score -= 8
        breakdown.append({"item": "声母", "delta": -8, "reason": f"声母重复 {initials}"})

    # 4. 韵母完全相同（拗口）
    finals = [p[-2:] if len(p) >= 2 else p for p in pinyins]
    if len(set(finals)) == 1:
        score -= 10
        breakdown.append({"item": "韵母", "delta": -10, "reason": f"韵母完全相同 {finals}"})

    raw = max(0.0, min(100.0, score))
    return DimensionScore(
        name="音律读音",
        raw_score=round(raw, 1),
        weighted_score=round(raw * DEFAULT_WEIGHTS["phonetic"], 2),
        breakdown=breakdown,
    )


# ============================================================
# ⑤ 字形书写评分（0-100，权重 10%）
# ============================================================
def score_visual(chars: list[dict]) -> DimensionScore:
    breakdown = []
    score = 70.0

    strokes = [c["kangxi"] for c in chars]
    # 笔画悬殊（差距过大）扣分
    if len(strokes) >= 2:
        diff = max(strokes) - min(strokes)
        if diff > 10:
            score -= 8
            breakdown.append({"item": "笔画均衡", "delta": -8,
                             "reason": f"笔画悬殊 {strokes}"})
        elif diff <= 4:
            score += 6
            breakdown.append({"item": "笔画均衡", "delta": +6,
                             "reason": f"笔画均衡 {strokes}"})

    # 总笔画过多
    total = sum(strokes)
    if total > 35:
        score -= 5
        breakdown.append({"item": "书写难度", "delta": -5,
                         "reason": f"笔画过多 {total}"})
    elif total <= 28:
        score += 5
        breakdown.append({"item": "书写难度", "delta": +5,
                         "reason": f"笔画适中 {total}"})

    # 偏旁重复扣分
    radicals = [c.get("radical") for c in chars if c.get("radical")]
    if len(radicals) >= 2 and len(set(radicals)) < len(radicals):
        score -= 6
        breakdown.append({"item": "偏旁", "delta": -6,
                         "reason": f"偏旁重复 {radicals}"})

    raw = max(0.0, min(100.0, score))
    return DimensionScore(
        name="字形书写",
        raw_score=round(raw, 1),
        weighted_score=round(raw * DEFAULT_WEIGHTS["visual"], 2),
        breakdown=breakdown,
    )


# ============================================================
# 综合评分入口
# ============================================================
def score_name(
    surname: str,
    given_chars: list[str],
    naming_wuxing: dict,
    gender: str = "男",
    style_prefs: Optional[list[str]] = None,
) -> NameScore:
    """
    给定姓+名+用神，返回完整五维评分。

    Args:
        surname: 姓氏，如 "张"
        given_chars: 名字单字列表，如 ["维","城"]
        naming_wuxing: get_naming_wuxing(bazi) 的返回值
        gender: "男" or "女"
        style_prefs: 风格偏好标签 ["典雅", "大气"]
    """
    # 1. 查字
    surname_info = get_char(surname)
    if not surname_info:
        raise ValueError(f"字库中找不到姓氏「{surname}」")

    char_infos = []
    for c in given_chars:
        info = get_char(c)
        if not info:
            raise ValueError(f"字库中找不到字「{c}」")
        char_infos.append(info)

    # 2. 五格计算
    wuge = compute_wuge(
        surname_info["kangxi"],
        [c["kangxi"] for c in char_infos],
        gender=gender,
    )

    # 3. 五维评分
    s_bazi = score_bazi(char_infos, naming_wuxing)
    s_wuge = score_wuge_sancai(wuge, gender)
    s_meaning = score_meaning(char_infos, style_prefs)
    s_phonetic = score_phonetic(surname_info, char_infos)
    s_visual = score_visual(char_infos)

    total = (s_bazi.weighted_score + s_wuge.weighted_score
             + s_meaning.weighted_score + s_phonetic.weighted_score
             + s_visual.weighted_score)

    return NameScore(
        full_name=surname + "".join(given_chars),
        surname=surname,
        given_chars=given_chars,
        bazi=s_bazi, wuge=s_wuge, meaning=s_meaning,
        phonetic=s_phonetic, visual=s_visual,
        total_score=round(total, 2),
        wuge_result=wuge.to_dict(),
    )


if __name__ == "__main__":
    # 测试用例：本项目宝宝的几个候选名字
    naming_wuxing = {
        "primary": "火",
        "secondary": "火",  # 壬水冬生，主次都需火
        "avoid": ["水"],
        "reasoning": "壬水生于丑月，冰冻急需丙丁火"
    }

    test_names = [
        ("张", ["维", "城"]),
        ("张", ["敦", "翔"]),
        ("张", ["景", "尧"]),
        ("张", ["珂", "玮"]),
        ("张", ["昊", "轩"]),
    ]

    print(f"{'='*70}")
    print("综合评分测试（宝宝：壬水丑月，用神火）")
    print(f"{'='*70}")
    print(f"{'名字':<8} {'总分':<8} {'八字':<8} {'五格':<8} {'字义':<8} {'音律':<8} {'字形':<8}")
    print(f"{'-'*70}")

    results = []
    for sn, gn in test_names:
        try:
            r = score_name(sn, gn, naming_wuxing, gender="男")
            results.append(r)
        except ValueError as e:
            print(f"⚠️  {sn}{''.join(gn)}: {e}")

    results.sort(key=lambda r: r.total_score, reverse=True)
    for r in results:
        print(f"{r.full_name:<6} {r.total_score:<8} "
              f"{r.bazi.raw_score:<8} {r.wuge.raw_score:<8} "
              f"{r.meaning.raw_score:<8} {r.phonetic.raw_score:<8} "
              f"{r.visual.raw_score:<8}")

    # 详细展示 Top 1
    if results:
        top = results[0]
        print(f"\n{'='*70}")
        print(f"详细评分卡：{top.full_name}（总分 {top.total_score}）")
        print(f"{'='*70}")
        for dim_name, dim in [("八字", top.bazi), ("五格", top.wuge),
                              ("字义", top.meaning), ("音律", top.phonetic),
                              ("字形", top.visual)]:
            print(f"\n● {dim_name}：{dim.raw_score}（权重后 {dim.weighted_score}）")
            for b in dim.breakdown:
                sign = "+" if b["delta"] >= 0 else ""
                print(f"    {b['item']}: {sign}{b['delta']} — {b['reason']}")
