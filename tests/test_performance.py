"""性能目标测试。"""
import time

from app.core.generator import GenerateRequest, generate_names


def test_generate_top10_under_two_seconds():
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
    assert elapsed < 2.0
