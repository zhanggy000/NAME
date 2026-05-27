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
from typing import Callable, Optional, Literal
import sqlite3
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "data" / "seed"))
sys.path.insert(0, str(_ROOT / "backend"))

from characters_seed import CHARACTERS_SEED, get_char, find_chars  # noqa: E402
from app.core.bazi import compute_bazi, get_naming_wuxing  # noqa: E402
from app.core.wuge import compute_wuge  # noqa: E402
from app.core.scoring import score_name, NameScore, get_surname_info  # noqa: E402


TraceCallback = Callable[[str], None]
POOL_PREVIEW_LIMIT = 100
NAME_DB_PATH = _ROOT / "data" / "name.db"

# When the primary and secondary naming elements collapse to the same element
# (for example winter Ren water wants fire twice), the generator expands the
# pool with nearby balancing elements. This keeps the search from becoming a
# one-note "fire + fire" list while still letting the score prefer the main
# yongshen.
BALANCE_EXPANSION = {
    "木": ["水", "火"],
    "火": ["木", "土"],
    "土": ["火", "金"],
    "金": ["土", "水"],
    "水": ["金", "木"],
}


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
    weights: Optional[dict[str, float]] = None     # 五维权重
    llm_config: Optional[dict[str, str]] = None     # 请求级 LLM 配置
    name_length: int = 2                            # 名字字数（不含姓）
    top_n: int = 10                                 # 返回前 N 个


def _format_trace_delta(delta: float | int) -> str:
    """Format scoring deltas for the browser console trace."""
    return f"+{delta}" if delta >= 0 else str(delta)


def _load_name_char_frequency() -> dict[str, int]:
    """Load real given-name character frequencies when the local DB is present."""
    if not NAME_DB_PATH.exists():
        return {}
    try:
        with sqlite3.connect(NAME_DB_PATH) as conn:
            rows = conn.execute("SELECT char, total_count FROM name_char_stats").fetchall()
    except sqlite3.Error:
        return {}
    return {char: int(total_count) for char, total_count in rows}


def _name_char_stats_summary(freq: dict[str, int]) -> dict:
    seed_chars = {c["char"] for c in CHARACTERS_SEED}
    naming_seed_chars = {c["char"] for c in CHARACTERS_SEED if c.get("style_tags")}
    return {
        "stats_chars": len(freq),
        "stats_with_seed_metadata": len(seed_chars & set(freq)),
        "stats_with_naming_metadata": len(naming_seed_chars & set(freq)),
    }


def _pool_summary(
    req: GenerateRequest,
    target_wuxings: list[str],
    avoid_wuxings: list[str],
    pool: list[dict],
    name_freq: Optional[dict[str, int]] = None,
) -> dict:
    """Summarize how the character pool was narrowed for trace output."""
    unique_targets = [wx for i, wx in enumerate(target_wuxings)
                      if wx and wx not in target_wuxings[:i]]
    naming_chars = [c for c in CHARACTERS_SEED if c.get("style_tags")]
    gender_chars = [
        c for c in naming_chars
        if c["gender_pref"] in (req.gender, "中性")
    ]
    target_chars = []
    seen = set()
    for wx in unique_targets:
        for ch in find_chars(wuxing=wx, gender=req.gender, style_tags=req.style_prefs):
            if ch["char"] in seen:
                continue
            seen.add(ch["char"])
            target_chars.append(ch)

    final_chars = {c["char"] for c in pool}
    removed = [c for c in target_chars if c["char"] not in final_chars]
    stats_summary = _name_char_stats_summary(name_freq or {})
    return {
        "total_seed": len(CHARACTERS_SEED),
        "naming_chars": len(naming_chars),
        "gender_chars": len(gender_chars),
        **stats_summary,
        "target_chars": len(target_chars),
        "final_chars": len(pool),
        "removed_chars": [c["char"] for c in removed],
        "unique_targets": unique_targets,
        "avoid_wuxings": avoid_wuxings,
    }


def _target_wuxings_for_generation(naming_wuxing: dict) -> list[str]:
    """Build a diversified search pool from the naming yongshen result."""
    primary = naming_wuxing.get("primary")
    secondary = naming_wuxing.get("secondary")
    avoid = set(naming_wuxing.get("avoid", []))
    targets = []

    for wx in [primary, secondary]:
        if wx and wx not in avoid and wx not in targets:
            targets.append(wx)

    if primary and primary == secondary:
        for wx in BALANCE_EXPANSION.get(primary, []):
            if wx not in avoid and wx not in targets:
                targets.append(wx)

    return targets


def _select_diverse_top(candidates: list[NameScore], top_n: int) -> list[NameScore]:
    """Pick high-scoring names while avoiding a repetitive top list."""
    selected = []
    first_char_counts: dict[str, int] = {}
    wuxing_pair_counts: dict[tuple[str, str], int] = {}

    for ns in candidates:
        if len(selected) >= top_n:
            break

        first = ns.given_chars[0]
        pair = tuple(get_char(ch)["wuxing"] for ch in ns.given_chars)
        if first_char_counts.get(first, 0) >= 2:
            continue
        if wuxing_pair_counts.get(pair, 0) >= max(3, top_n // 2):
            continue

        selected.append(ns)
        first_char_counts[first] = first_char_counts.get(first, 0) + 1
        wuxing_pair_counts[pair] = wuxing_pair_counts.get(pair, 0) + 1

    if len(selected) < top_n:
        seen = {ns.full_name for ns in selected}
        for ns in candidates:
            if len(selected) >= top_n:
                break
            if ns.full_name not in seen:
                selected.append(ns)
                seen.add(ns.full_name)

    return selected


def _build_execution_trace(
    req: GenerateRequest,
    bazi,
    naming_wuxing: dict,
    surname_info: dict,
    target_wuxings: list[str],
    avoid_wuxings: list[str],
    pool: list[dict],
    considered: int,
    candidates: list[NameScore],
    unique_candidates: list[NameScore],
    top_dicts: list[dict],
    reject_stats: dict[str, int],
) -> list[str]:
    """Build a Chinese console-style trace that mirrors the real generation pipeline."""
    name_freq = _load_name_char_frequency()
    summary = _pool_summary(req, target_wuxings, avoid_wuxings, pool, name_freq=name_freq)
    preview_count = min(POOL_PREVIEW_LIMIT, len(pool))
    preview = " ".join(c["char"] for c in pool[:POOL_PREVIEW_LIMIT])
    total_pairs = considered + reject_stats["same_char"]
    lines = [
        "开始生成：收到一次新的取名请求。",
        (
            "输入信息："
            f"姓氏「{req.surname}」，性别「{req.gender}」，"
            f"出生时间 {req.year:04d}-{req.month:02d}-{req.day:02d} "
            f"{req.hour:02d}:{req.minute:02d}，"
            f"{'农历' if req.is_lunar else '公历'}，返回前 {req.top_n} 个名字。"
        ),
        "",
        "第1步｜八字排盘：把出生时间换算成四柱八字，用来判断名字主要补什么五行。",
        f"  结果：四柱为「{bazi.bazi_string}」。",
        (
            "  逐柱："
            f"年柱 {bazi.year_gan}{bazi.year_zhi}，"
            f"月柱 {bazi.month_gan}{bazi.month_zhi}，"
            f"日柱 {bazi.day_gan}{bazi.day_zhi}，"
            f"时柱 {bazi.hour_gan}{bazi.hour_zhi}。"
        ),
        f"  日主：{bazi.day_master}，五行属{bazi.day_master_wuxing}；月令为{bazi.birth_month_zhi}月（{bazi.month_name}）。",
        f"  五行加权分布：{bazi.wuxing_score}。",
        "",
        "第2步｜确定取名用神：根据日主和月令，从调候规则里判断名字优先补的五行。",
        f"  主补五行：{naming_wuxing['primary']}；辅助五行：{naming_wuxing['secondary']}；尽量避开：{naming_wuxing.get('avoid', [])}。",
        f"  判断理由：{naming_wuxing.get('reasoning', '')}",
        "",
        "第3步｜建立候选字池：先查姓氏笔画，再按用神五行、性别和风格偏好筛出可用字。",
        (
            "  姓氏信息："
            f"「{surname_info['char']}」康熙笔画 {surname_info['kangxi']}，"
            f"五行属{surname_info['wuxing']}，声调 {surname_info['tone']}。"
        ),
        f"  当前种子字库总共有 {summary['total_seed']} 个字。",
        f"  其中标记为可取名的字有 {summary['naming_chars']} 个。",
        f"  适合「{req.gender}」或中性的可取名字有 {summary['gender_chars']} 个。",
        (
            f"  真实名用字统计库已有 {summary['stats_chars']} 个字；"
            f"其中 {summary['stats_with_seed_metadata']} 个已有完整五行/康熙/字义元数据，"
            f"{summary['stats_with_naming_metadata']} 个已标记为可直接进入生成器。"
        ),
        "  说明：真实姓名频率只能证明这个字被用作名字；进入生成器还必须补齐五行、康熙笔画、字义、性别气质和禁忌校对。",
        "  性别处理：候选池排除明确异性的字；评分时会按名字气质是否匹配性别继续加减分。",
        (
            f"  本次用神主方向是「{naming_wuxing['primary']}」，"
            f"为了避免名字过于单一，同时纳入 {summary['unique_targets']} 行字参与候选。"
        ),
        (
            f"  符合这些五行和性别条件的字有 {summary['target_chars']} 个。"
        ),
        (
            f"  再排除姓氏专用字、必避字和重复项后，"
            f"最终候选字池共有 {summary['final_chars']} 个字。"
        ),
        (
            f"  字池预览：共 {len(pool)} 个字，"
            f"下面显示前 {preview_count} 个。"
        ),
        f"  前 {preview_count} 个：{preview}",
        (
            "  被排除的候选字（多为姓氏专用字）："
            + (" ".join(summary["removed_chars"]) if summary["removed_chars"] else "无")
        ),
        "",
        "第4步｜组合和硬过滤：把候选字两两组合，先用三才五格排除明显不合适的组合。",
        f"  先枚举 {total_pairs} 个双字组合。",
        f"  因两个字重复排除 {reject_stats['same_char']} 个。",
        f"  实际进入三才五格检查的组合有 {considered} 个。",
        f"  因人格大凶排除 {reject_stats['renge_daxiong']} 个。",
        f"  因总格大凶排除 {reject_stats['zongge_daxiong']} 个。",
        f"  因地格大凶排除 {reject_stats['dige_daxiong']} 个。",
        f"  因三才相克严重排除 {reject_stats['sancai_xiong']} 个。",
        f"  因字库缺字或评分异常排除 {reject_stats['score_error']} 个。",
        f"  通过硬过滤并进入完整评分的名字有 {len(candidates)} 个。",
        "",
        "第5步｜五维评分和排序：对通过过滤的名字计算八字、五格、字义、音律、字形五项分数。",
        f"  去重后还有 {len(unique_candidates)} 个候选。",
        f"  按总分排序后，返回前 {len(top_dicts)} 个。",
        "",
        "候选名字逐项解释：",
    ]

    for index, candidate in enumerate(top_dicts, 1):
        scores = candidate["scores"]
        wuge = candidate["wuge_result"]
        lines.extend([
            f"第 {index} 名：{candidate['full_name']}，总分 {candidate['total_score']}。",
            (
                "  三才五格："
                f"天格{wuge['tiange']}，人格{wuge['renge']}，地格{wuge['dige']}，"
                f"外格{wuge['waige']}，总格{wuge['zongge']}；"
                f"三才 {wuge['sancai_heaven']}-{wuge['sancai_person']}-{wuge['sancai_earth']} "
                f"，判定为{wuge['sancai_relation']['rating']}。"
            ),
        ])
        for key in ["bazi", "wuge", "meaning", "phonetic", "visual"]:
            score = scores[key]
            lines.append(
                f"  {score['name']}：原始分 {score['raw_score']}，计入总分 {score['weighted_score']}。"
            )
            for item in score.get("breakdown", []):
                lines.append(
                    "    "
                    f"{item['item']}：{_format_trace_delta(item['delta'])}，"
                    f"{item['reason']}"
                )
        highlight = candidate.get("highlight")
        if highlight:
            lines.append(f"  推荐摘要：{highlight}")
        issues = candidate.get("issues") or []
        if issues:
            lines.append(f"  注意事项：{'；'.join(issues)}")
        lines.append("")

    lines.append("生成完成：以上就是本次请求的完整执行过程。")
    return lines


def _emit(trace_callback: Optional[TraceCallback], message: str) -> None:
    if trace_callback:
        trace_callback(message)


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


def _sort_pool_by_name_frequency(pool: list[dict], name_freq: dict[str, int]) -> list[dict]:
    if not name_freq:
        return pool
    return sorted(pool, key=lambda ch: (-name_freq.get(ch["char"], 0), ch["kangxi"], ch["char"]))


def generate_names(
    req: GenerateRequest,
    trace_callback: Optional[TraceCallback] = None,
) -> dict:
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
    _emit(trace_callback, "开始生成：后端已收到请求，先读取出生信息和偏好。")
    _emit(
        trace_callback,
        (
            f"输入信息：姓氏「{req.surname}」，性别「{req.gender}」，"
            f"出生时间 {req.year:04d}-{req.month:02d}-{req.day:02d} {req.hour:02d}:{req.minute:02d}，"
            f"{'农历' if req.is_lunar else '公历'}。"
        ),
    )

    # === 步骤 1-2：排八字 + 定用神 ===
    _emit(trace_callback, "第1步｜八字排盘：把出生时间换算成四柱八字。")
    bazi = compute_bazi(
        req.year, req.month, req.day, req.hour, req.minute,
        is_lunar=req.is_lunar, gender=req.gender,
    )
    _emit(
        trace_callback,
        (
            f"八字排盘完成：四柱为「{bazi.bazi_string}」，"
            f"日主是{bazi.day_master}，五行属{bazi.day_master_wuxing}，"
            f"生于{bazi.birth_month_zhi}月（{bazi.month_name}）。"
        ),
    )
    _emit(trace_callback, f"五行加权分布：{bazi.wuxing_score}。")

    _emit(trace_callback, "第2步｜确定取名用神：根据日主和月令判断名字优先补什么五行。")
    naming_wuxing = get_naming_wuxing(bazi)
    _emit(
        trace_callback,
        (
            f"用神判断完成：主补「{naming_wuxing['primary']}」，"
            f"辅助「{naming_wuxing['secondary']}」，"
            f"尽量避开 {naming_wuxing.get('avoid', [])}。"
        ),
    )
    _emit(trace_callback, f"判断理由：{naming_wuxing.get('reasoning', '')}")

    # === 步骤 3：选五行 ===
    target_wuxings = _target_wuxings_for_generation(naming_wuxing)
    avoid_wuxings = naming_wuxing.get("avoid", [])

    # === 必含字处理 ===
    must_char_info = None
    if req.must_include:
        _emit(trace_callback, f"处理必含字：用户要求名字里包含「{req.must_include}」。")
        must_char_info = get_char(req.must_include)
        if not must_char_info:
            raise ValueError(f"必含字「{req.must_include}」不在字库中")
        _emit(
            trace_callback,
            f"必含字校验通过：「{req.must_include}」在字库中，康熙笔画 {must_char_info['kangxi']}。",
        )

    # === 步骤 4：笔画穷举 + 五行字筛选 ===
    _emit(trace_callback, "第3步｜建立候选字池：先查姓氏，再按用神五行筛字。")
    surname_info = get_surname_info(req.surname)
    sn_strokes = surname_info["kangxi"]
    _emit(
        trace_callback,
        (
            f"姓氏信息：「{req.surname}」康熙笔画为 {sn_strokes}，"
            f"五行属{surname_info['wuxing']}。"
        ),
    )

    # 候选字池（按用神五行筛）
    avoid_set = set(req.must_avoid or [])
    if req.must_include:
        avoid_set.add(req.must_include)  # 已经固定不重复加
    pool = _filter_chars_by_wuxing_pool(
        target_wuxings, req.gender, req.style_prefs,
        exclude=avoid_set,
    )
    name_freq = _load_name_char_frequency()
    pool = _sort_pool_by_name_frequency(pool, name_freq)
    summary = _pool_summary(req, target_wuxings, avoid_wuxings, pool, name_freq=name_freq)
    _emit(
        trace_callback,
        (
            f"当前种子字库共有 {summary['total_seed']} 个字；"
            f"可取名字 {summary['naming_chars']} 个；"
            f"适合「{req.gender}」或中性的可取名字 {summary['gender_chars']} 个。"
        ),
    )
    if summary["stats_chars"]:
        _emit(
            trace_callback,
            (
                f"真实名用字统计库已有 {summary['stats_chars']} 个字；"
                f"其中 {summary['stats_with_seed_metadata']} 个已有完整取名元数据，"
                f"{summary['stats_with_naming_metadata']} 个已标记为可直接进入生成器。"
                " 当前不会直接使用未校对的频率字，避免缺五行、缺字义或含禁忌字。"
            ),
        )
    _emit(
        trace_callback,
        (
            "性别处理：候选池会排除明确异性的字；完整评分时还会按性别气质加减分，"
            + ("女名会优先奖励婉约、清丽、柔美、灵动等气质。" if req.gender == "女"
               else "男名会优先奖励大气、刚毅、厚重、进取等气质。")
        ),
    )
    _emit(
        trace_callback,
        (
            f"本次主用神是「{naming_wuxing['primary']}」。"
            f"为避免名字全部集中在单一五行，候选阶段同时纳入 {summary['unique_targets']} 行字。"
        ),
    )
    _emit(
        trace_callback,
        (
            f"符合这些五行和性别条件的字有 {summary['target_chars']} 个。"
            f"最终评分仍会让主用神「{naming_wuxing['primary']}」占更高权重。"
        ),
    )

    # 如果用神字数不足，放宽到不在 avoid 的所有字
    if len(pool) < 5:
        _emit(trace_callback, "候选字池少于 5 个，放宽规则：改为使用不属于忌神五行的可取名字。")
        pool = [c for c in CHARACTERS_SEED
                if c.get("style_tags")  # 非姓氏字
                and c["wuxing"] not in avoid_wuxings
                and c["char"] not in avoid_set
                and (c["gender_pref"] in (req.gender, "中性"))]
        summary = _pool_summary(req, target_wuxings, avoid_wuxings, pool)
        _emit(trace_callback, f"放宽后候选字池有 {len(pool)} 个字。")

    preview_count = min(POOL_PREVIEW_LIMIT, len(pool))
    preview = " ".join(c["char"] for c in pool[:POOL_PREVIEW_LIMIT])
    _emit(
        trace_callback,
        (
            f"最终候选字池共有 {len(pool)} 个字。"
            f"下面显示前 {preview_count} 个。"
        ),
    )
    _emit(trace_callback, f"字池前 {preview_count} 个：{preview}")
    if summary["removed_chars"]:
        _emit(trace_callback, "被排除的候选字（多为姓氏专用字）：" + " ".join(summary["removed_chars"]))

    # === 构造候选名字（笛卡尔积，考虑必含字位置）===
    candidates = []  # 列表存 (char_list, NameScore)
    considered = 0
    reject_stats = {
        "same_char": 0,
        "renge_daxiong": 0,
        "zongge_daxiong": 0,
        "dige_daxiong": 0,
        "sancai_xiong": 0,
        "score_error": 0,
    }

    if req.name_length == 2:
        _emit(trace_callback, "第4步｜组合和硬过滤：把候选字两两组合，并先检查三才五格。")
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
                        reject_stats["same_char"] += 1
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
                        reject_stats["renge_daxiong"] += 1
                        continue
                    if wuge.zongge_info["level"] == "大凶":
                        reject_stats["zongge_daxiong"] += 1
                        continue
                    if wuge.dige_info["level"] == "大凶":
                        reject_stats["dige_daxiong"] += 1
                        continue
                    if wuge.sancai_relation["rating"] == "凶":
                        reject_stats["sancai_xiong"] += 1
                        continue

                    # 五格通过 → 完整评分
                    try:
                        ns = score_name(
                            req.surname,
                            [chars[0]["char"], chars[1]["char"]],
                            naming_wuxing, gender=req.gender,
                            style_prefs=req.style_prefs,
                            weights=req.weights,
                        )
                        candidates.append(ns)
                    except ValueError:
                        reject_stats["score_error"] += 1
                        continue

                # 单遍 fixed_first 不需要外层 c2 循环
                if mode == "fixed_first":
                    break
            if mode == "fixed_second":
                pass  # 内层 c1 已遍历
    else:
        raise NotImplementedError("当前仅支持双字名")

    total_pairs = considered + reject_stats["same_char"]
    _emit(trace_callback, f"组合检查完成：先枚举 {total_pairs} 个双字组合。")
    _emit(
        trace_callback,
        (
            "硬过滤统计："
            f"重复字 {reject_stats['same_char']} 个，"
            f"实际进入五格检查 {considered} 个，"
            f"人格大凶 {reject_stats['renge_daxiong']} 个，"
            f"总格大凶 {reject_stats['zongge_daxiong']} 个，"
            f"地格大凶 {reject_stats['dige_daxiong']} 个，"
            f"三才严重相克 {reject_stats['sancai_xiong']} 个。"
        ),
    )
    _emit(trace_callback, f"通过硬过滤并完成五维评分的候选有 {len(candidates)} 个。")

    # === 步骤 5-7（部分）：排序去重 ===
    _emit(trace_callback, "第5步｜排序去重：把候选名字按总分从高到低排序。")
    seen_names = set()
    unique_candidates = []
    for ns in sorted(candidates, key=lambda x: x.total_score, reverse=True):
        if ns.full_name in seen_names:
            continue
        seen_names.add(ns.full_name)
        unique_candidates.append(ns)

    top = _select_diverse_top(unique_candidates, req.top_n)
    top_dicts = [ns.to_dict() for ns in top]
    _emit(trace_callback, f"排序完成：去重后 {len(unique_candidates)} 个候选，准备返回前 {len(top)} 个。")
    _emit(trace_callback, "多样性处理：Top 名单会限制同一个首字和同一种五行组合过度重复。")

    for index, candidate in enumerate(top_dicts[: min(5, len(top_dicts))], 1):
        _emit(
            trace_callback,
            (
                f"Top {index}：{candidate['full_name']}，总分 {candidate['total_score']}；"
                f"八字 {candidate['scores']['bazi']['raw_score']}，"
                f"五格 {candidate['scores']['wuge']['raw_score']}，"
                f"字义 {candidate['scores']['meaning']['raw_score']}，"
                f"音律 {candidate['scores']['phonetic']['raw_score']}，"
                f"字形 {candidate['scores']['visual']['raw_score']}。"
            ),
        )

    trace = _build_execution_trace(
        req=req,
        bazi=bazi,
        naming_wuxing=naming_wuxing,
        surname_info=surname_info,
        target_wuxings=target_wuxings,
        avoid_wuxings=avoid_wuxings,
        pool=pool,
        considered=considered,
        candidates=candidates,
        unique_candidates=unique_candidates,
        top_dicts=top_dicts,
        reject_stats=reject_stats,
    )

    return {
        "bazi": bazi.to_dict(),
        "naming_wuxing": naming_wuxing,
        "candidates": top_dicts,
        "stats": {
            "pool_size": len(pool),
            "considered": considered,
            "valid_wuge": len(candidates),
            "unique": len(unique_candidates),
            "returned": len(top),
        },
        "trace": trace,
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
