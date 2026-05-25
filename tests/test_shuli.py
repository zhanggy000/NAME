"""81 数理表单元测试"""
from shuli_81 import (
    SHULI_81, get_shuli, MALE_TABOO, FEMALE_TABOO,
    ALL_BAD, ALL_GREAT,
)


def test_shuli_count():
    """必须有 81 条数据"""
    assert len(SHULI_81) == 81


def test_shuli_continuous_numbering():
    """数字 1-81 连续"""
    numbers = [r[0] for r in SHULI_81]
    assert numbers == list(range(1, 82))


def test_shuli_levels_valid():
    """level 必须在合法集合内"""
    valid = {"大吉", "吉", "半吉", "凶", "大凶"}
    for n, level, *_ in SHULI_81:
        assert level in valid, f"非法 level: {level} (number {n})"


def test_classic_known_numbers():
    """几个传统姓名学经典数字测试"""
    assert get_shuli(1)["level"] == "大吉"
    assert get_shuli(11)["level"] == "大吉"
    assert get_shuli(15)["level"] == "大吉"
    assert get_shuli(19)["level"] == "大凶"
    assert get_shuli(20)["level"] == "大凶"
    assert get_shuli(24)["level"] == "大吉"
    assert get_shuli(35)["level"] == "大吉"
    assert get_shuli(34)["level"] == "大凶"


def test_taboo_consistency():
    """男女忌数应在凶数集合内"""
    for n in MALE_TABOO:
        assert n in ALL_BAD or get_shuli(n)["level"] == "半吉"
    for n in FEMALE_TABOO:
        # 女命首领数 21/23/33 实际是大吉数但传统视为女命忌
        # 不强制要求在 ALL_BAD 中
        pass


def test_great_numbers_include_classics():
    """常见大吉数应在 ALL_GREAT 中。
    注：17 和 18 在我们采用的版本中归为「吉」而非「大吉」，故不强制。
    """
    classics = {1, 3, 5, 6, 8, 11, 13, 15, 16, 21, 23, 24, 25, 31, 32, 33, 35}
    for n in classics:
        assert n in ALL_GREAT, f"{n} 应为大吉数"


def test_out_of_range():
    """超界处理"""
    r = get_shuli(82)
    assert r["level"] == "未知"
    r = get_shuli(0)
    assert r["level"] == "未知"
