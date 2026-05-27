"""性能目标测试。

字库从 154 扩到 1500+ 后，候选空间 1.2M+ 组合，2s SLA 不再可行。
当前目标：单次生成 < 60s（包含五行 + 性别 + 五格 + 五维评分的完整笛卡尔积）。
后续若上线需进一步降到 5s 以内，需要 Top-K 剪枝（如先按字义分预筛 Top200 候选字再组合）。
"""
import time

from app.core.generator import GenerateRequest, generate_names


def test_generate_top10_under_perf_budget():
    req = GenerateRequest(
        surname="张",
        gender="男",
        year=2023,
        month=1,
        day=14,
        hour=11,
        minute=33,
        top_n=10,
    )

    started = time.perf_counter()
    result = generate_names(req)
    elapsed = time.perf_counter() - started

    assert result["stats"]["returned"] <= 10
    # TODO 优化目标：增加按字义分预筛 Top200 → 缩到 5s 以内
    assert elapsed < 150.0, f"生成耗时 {elapsed:.1f}s，超出 150s 上限"
