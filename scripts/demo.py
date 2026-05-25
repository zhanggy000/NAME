"""
快速演示脚本：跑几个典型场景，输出结果。
便于 README/demo 截图，也是 smoke test。
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT / "data" / "seed"))

from app.core.bazi import compute_bazi, get_naming_wuxing
from app.core.generator import generate_names, GenerateRequest


SCENARIOS = [
    {
        "title": "场景 1：本项目男宝（壬水冬生）",
        "req": GenerateRequest(
            surname="张", gender="男",
            year=2023, month=1, day=14, hour=11, minute=33,
            is_lunar=False, top_n=5,
        ),
    },
    {
        "title": "场景 2：女宝末字必含「雯」",
        "req": GenerateRequest(
            surname="张", gender="女",
            year=2026, month=5, day=25, hour=14, minute=30,
            is_lunar=False, must_include="雯", must_include_position="second",
            top_n=5,
        ),
    },
    {
        "title": "场景 3：男宝典雅风格",
        "req": GenerateRequest(
            surname="李", gender="男",
            year=2025, month=10, day=15, hour=9, minute=0,
            is_lunar=False, style_prefs=["典雅", "古意"],
            top_n=5,
        ),
    },
    {
        "title": "场景 4：女宝大气稳重",
        "req": GenerateRequest(
            surname="王", gender="女",
            year=2024, month=8, day=8, hour=14, minute=0,
            is_lunar=False, style_prefs=["大气", "稳重"],
            top_n=5,
        ),
    },
]


def main():
    print("=" * 80)
    print("NAME 智能取名系统 · 演示")
    print("=" * 80)

    for s in SCENARIOS:
        print(f"\n\n{'-' * 80}")
        print(f"【{s['title']}】")
        print(f"{'-' * 80}")

        result = generate_names(s["req"])
        bz = result["bazi"]
        nw = result["naming_wuxing"]

        print(f"八字：{bz['bazi_string']}  "
              f"日主：{bz['day_master']}({bz['day_master_wuxing']})  "
              f"月令：{bz['birth_month_zhi']}({bz['month_name']})")
        print(f"用神：{nw['primary']}/{nw['secondary']}  忌：{nw['avoid']}")
        print()

        print(f"{'排名':<5}{'名字':<10}{'总分':<8}{'八字':<6}{'五格':<6}{'字义':<6}{'音律':<6}{'字形':<6}{'亮点'}")
        print("─" * 78)
        for i, c in enumerate(result["candidates"], 1):
            ss = c["scores"]
            hl = c.get("highlight", "")[:30]
            print(f"{i:<5}{c['full_name']:<8}"
                  f"{c['total_score']:<8.1f}"
                  f"{ss['bazi']['raw_score']:<6.0f}"
                  f"{ss['wuge']['raw_score']:<6.0f}"
                  f"{ss['meaning']['raw_score']:<6.0f}"
                  f"{ss['phonetic']['raw_score']:<6.0f}"
                  f"{ss['visual']['raw_score']:<6.0f}{hl}")

    print(f"\n{'=' * 80}")
    print("演示完成。")
    print("启动后端：cd backend && uvicorn app.main:app --reload")
    print("启动前端：cd frontend && npm install && npm run dev")
    print("CLI 用法：python scripts/cli.py --help")


if __name__ == "__main__":
    main()
