"""
NAME 命令行工具

用法示例：
    # 排八字
    python scripts/cli.py bazi 2023-01-14 11:33 --gender 男

    # 生成名字
    python scripts/cli.py gen 张 男 2023-01-14 11:33 --top 10

    # 必含字
    python scripts/cli.py gen 张 女 2026-05-25 14:30 --must 雯 --pos second

    # 给具体名字打分
    python scripts/cli.py score 张 维城 男 2023-01-14 11:33

    # 查字
    python scripts/cli.py char 雯
"""
import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT / "data" / "seed"))

from characters_seed import get_char  # noqa: E402
from app.core.bazi import compute_bazi, get_naming_wuxing  # noqa: E402
from app.core.scoring import score_name  # noqa: E402
from app.core.generator import generate_names, GenerateRequest  # noqa: E402


# ANSI 颜色
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def _parse_dt(date_s: str, time_s: str):
    """'2023-01-14' '11:33' → (2023,1,14,11,33)"""
    y, m, d = [int(x) for x in date_s.split("-")]
    h, mi = [int(x) for x in time_s.split(":")]
    return y, m, d, h, mi


def cmd_bazi(args):
    y, m, d, h, mi = _parse_dt(args.date, args.time)
    r = compute_bazi(y, m, d, h, mi, is_lunar=args.lunar, gender=args.gender)
    nw = get_naming_wuxing(r)

    print(f"{C.BOLD}{'='*60}{C.RESET}")
    print(f"{C.BOLD}八字排盘  {args.date} {args.time} {'农' if args.lunar else '公'}历 {args.gender}{C.RESET}")
    print(f"{C.BOLD}{'='*60}{C.RESET}")
    print(f"四柱：{C.CYAN}{r.bazi_string}{C.RESET}")
    print(f"日主：{C.YELLOW}{r.day_master}{C.RESET}（{r.day_master_wuxing}）"
          f"生于 {r.birth_month_zhi}月（{r.month_name}）")
    print(f"\n五行分布（含地支藏干加权）：")
    for wx in ["木", "火", "土", "金", "水"]:
        c = r.wuxing_count[wx]
        s = r.wuxing_score[wx]
        bar = "█" * int(s) + "▌" * (1 if s % 1 >= 0.5 else 0)
        print(f"  {wx}: {c} 个  {bar}  ({s})")

    print(f"\n{C.GREEN}取名用神：{C.RESET}")
    print(f"  主用神：{C.BOLD}{nw['primary']}{C.RESET}（推荐补此五行）")
    print(f"  次用神：{nw['secondary']}")
    if nw['avoid']:
        print(f"  {C.RED}忌神：{','.join(nw['avoid'])}（避免此五行）{C.RESET}")
    print(f"\n  理由：{C.DIM}{nw['reasoning']}{C.RESET}")


def cmd_gen(args):
    y, m, d, h, mi = _parse_dt(args.date, args.time)
    req = GenerateRequest(
        surname=args.surname,
        gender=args.gender,
        year=y, month=m, day=d, hour=h, minute=mi,
        is_lunar=args.lunar,
        must_include=args.must,
        must_include_position=args.pos,
        must_avoid=args.avoid.split(",") if args.avoid else None,
        style_prefs=args.style.split(",") if args.style else None,
        top_n=args.top,
    )
    result = generate_names(req)

    bz = result["bazi"]
    nw = result["naming_wuxing"]
    s = result["stats"]

    print(f"{C.BOLD}{'='*72}{C.RESET}")
    print(f"{C.BOLD}「{args.surname}」姓{args.gender}宝宝候选名 Top {s['returned']}{C.RESET}")
    print(f"{C.BOLD}{'='*72}{C.RESET}")
    print(f"八字：{C.CYAN}{bz['bazi_string']}{C.RESET}  "
          f"日主：{bz['day_master']}({bz['day_master_wuxing']})  "
          f"{bz['birth_month_zhi']}月")
    print(f"用神：{C.GREEN}{nw['primary']}/{nw['secondary']}{C.RESET}  "
          f"忌：{C.RED}{','.join(nw['avoid']) if nw['avoid'] else '无'}{C.RESET}")
    if args.must:
        print(f"必含字：{C.MAGENTA}{args.must}{C.RESET}（位置：{args.pos}）")
    print(f"候选池：{s['pool_size']} 字 → 五格通过 {s['valid_wuge']} → Top {s['returned']}")

    print(f"\n{C.BOLD}{'排名':<5}{'名字':<10}{'总分':<8}{'八字':<6}{'五格':<6}{'字义':<6}{'音律':<6}{'字形':<6}{C.RESET}")
    print("─" * 72)
    for i, c in enumerate(result["candidates"], 1):
        ss = c["scores"]
        # 颜色：金牌银牌铜牌
        rank_color = [C.YELLOW, C.CYAN, C.MAGENTA][i-1] if i <= 3 else ""
        print(f"{rank_color}{i:<5}{c['full_name']:<8}{C.RESET}"
              f"{C.BOLD}{c['total_score']:<8}{C.RESET}"
              f"{ss['bazi']['raw_score']:<6}"
              f"{ss['wuge']['raw_score']:<6}"
              f"{ss['meaning']['raw_score']:<6}"
              f"{ss['phonetic']['raw_score']:<6}"
              f"{ss['visual']['raw_score']:<6}")

    # 详细展示 Top 1
    if result["candidates"]:
        top = result["candidates"][0]
        print(f"\n{C.BOLD}━━━ Top 1 详情：{top['full_name']}（{top['total_score']} 分）━━━{C.RESET}")
        for dim_key, dim_label in [("bazi","八字补益"), ("wuge","三才五格"),
                                    ("meaning","字义寓意"), ("phonetic","音律读音"),
                                    ("visual","字形书写")]:
            dim = top["scores"][dim_key]
            print(f"\n{C.CYAN}● {dim_label}：{dim['raw_score']}{C.RESET}"
                  f" {C.DIM}(权重后 {dim['weighted_score']}){C.RESET}")
            for b in dim["breakdown"]:
                sign = "+" if b["delta"] >= 0 else ""
                color = C.GREEN if b["delta"] >= 0 else C.RED
                print(f"    {b['item']}: {color}{sign}{b['delta']}{C.RESET} {b['reason']}")


def cmd_score(args):
    y, m, d, h, mi = _parse_dt(args.date, args.time)
    bz = compute_bazi(y, m, d, h, mi, is_lunar=args.lunar, gender=args.gender)
    nw = get_naming_wuxing(bz)

    given = list(args.given)
    s = score_name(args.surname, given, nw, gender=args.gender)

    print(f"{C.BOLD}{'='*60}{C.RESET}")
    print(f"{C.BOLD}名字评分：{s.full_name}{C.RESET}")
    print(f"{C.BOLD}{'='*60}{C.RESET}")
    print(f"八字：{bz.bazi_string}  日主：{bz.day_master}({bz.day_master_wuxing})")
    print(f"用神：{nw['primary']}/{nw['secondary']}，忌：{nw['avoid']}")
    print(f"\n{C.BOLD}总分：{s.total_score}{C.RESET} / 100")
    print(f"\n  八字补益：{s.bazi.raw_score:5.1f}  (×0.30 → {s.bazi.weighted_score})")
    print(f"  三才五格：{s.wuge.raw_score:5.1f}  (×0.25 → {s.wuge.weighted_score})")
    print(f"  字义寓意：{s.meaning.raw_score:5.1f}  (×0.20 → {s.meaning.weighted_score})")
    print(f"  音律读音：{s.phonetic.raw_score:5.1f}  (×0.15 → {s.phonetic.weighted_score})")
    print(f"  字形书写：{s.visual.raw_score:5.1f}  (×0.10 → {s.visual.weighted_score})")

    if args.verbose:
        for dim_key, dim_label in [("bazi","八字"), ("wuge","五格"),
                                    ("meaning","字义"), ("phonetic","音律"),
                                    ("visual","字形")]:
            dim = getattr(s, dim_key)
            print(f"\n{C.CYAN}● {dim_label}：{C.RESET}")
            for b in dim.breakdown:
                sign = "+" if b["delta"] >= 0 else ""
                color = C.GREEN if b["delta"] >= 0 else C.RED
                print(f"    {b['item']}: {color}{sign}{b['delta']}{C.RESET} {b['reason']}")


def cmd_char(args):
    info = get_char(args.char)
    if not info:
        print(f"{C.RED}字「{args.char}」不在字库中{C.RESET}")
        return
    print(f"{C.BOLD}{info['char']}{C.RESET} ({info['pinyin']} 第{info['tone']}声)")
    print(f"  康熙{info['kangxi']}画 / 简体{info['simplified']}画")
    print(f"  五行：{C.CYAN}{info['wuxing']}{C.RESET}  部首：{info.get('radical','?')}")
    print(f"  本义：{info['meaning']}")
    print(f"  适用：{info['gender_pref']}  标签：{','.join(info.get('style_tags',[]))}")
    if info.get('classics_refs'):
        print(f"\n  {C.GREEN}典籍出处：{C.RESET}")
        for c in info['classics_refs']:
            print(f"    • {c}")
    if info.get('famous_refs'):
        print(f"\n  {C.MAGENTA}同字名人：{C.RESET}")
        for f in info['famous_refs']:
            print(f"    • {f}")


def main():
    p = argparse.ArgumentParser(description="NAME 智能取名命令行工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    # bazi
    pb = sub.add_parser("bazi", help="排八字")
    pb.add_argument("date", help="YYYY-MM-DD")
    pb.add_argument("time", help="HH:MM")
    pb.add_argument("--gender", default="男", choices=["男", "女"])
    pb.add_argument("--lunar", action="store_true", help="使用农历")
    pb.set_defaults(func=cmd_bazi)

    # gen
    pg = sub.add_parser("gen", help="生成名字 Top N")
    pg.add_argument("surname")
    pg.add_argument("gender", choices=["男", "女"])
    pg.add_argument("date", help="YYYY-MM-DD")
    pg.add_argument("time", help="HH:MM")
    pg.add_argument("--lunar", action="store_true")
    pg.add_argument("--must", help="必含字")
    pg.add_argument("--pos", default="any", choices=["first","second","any"])
    pg.add_argument("--avoid", help="必避字，逗号分隔")
    pg.add_argument("--style", help="风格标签，逗号分隔，如 典雅,大气")
    pg.add_argument("--top", type=int, default=10)
    pg.set_defaults(func=cmd_gen)

    # score
    ps = sub.add_parser("score", help="给具体名字打分")
    ps.add_argument("surname")
    ps.add_argument("given", help="名字（不含姓），如 维城")
    ps.add_argument("gender", choices=["男", "女"])
    ps.add_argument("date")
    ps.add_argument("time")
    ps.add_argument("--lunar", action="store_true")
    ps.add_argument("-v", "--verbose", action="store_true", help="显示评分细节")
    ps.set_defaults(func=cmd_score)

    # char
    pc = sub.add_parser("char", help="查询单字")
    pc.add_argument("char", help="要查的字")
    pc.set_defaults(func=cmd_char)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
