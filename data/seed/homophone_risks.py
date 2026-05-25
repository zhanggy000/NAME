"""
谐音风险词库

记录常见取名时需要避开的谐音组合。
格式：(name_pattern, sounds_like, language, severity, category, note)
"""

HOMOPHONE_RISKS = [
    # ===== 普通话经典谐音坑 =====
    ("范统",   "饭桶",  "普通话", "high",   "搞笑", "千古名梗"),
    ("史珍香", "屎真香", "普通话", "high",   "不雅", "极度不雅"),
    ("杜子腾", "肚子疼", "普通话", "high",   "搞笑", ""),
    ("朱逸群", "猪一群", "普通话", "high",   "搞笑", ""),
    ("吴用",   "无用",  "普通话", "medium", "负面", "本身亦水浒人物"),
    ("姚明",   "妖明",  "普通话", "low",    "搞笑", "已是知名人物，不构成实际风险"),
    ("沈京兵", "神经病", "普通话", "high",   "不雅", ""),
    ("胡丽晶", "狐狸精", "普通话", "high",   "不雅", ""),
    ("沙碧",   "傻屄",  "普通话", "high",   "不雅", ""),
    ("孙艳秋", "孙颜抽", "普通话", "low",    "搞笑", ""),

    # ===== 张姓需注意的谐音 =====
    ("张治国", "找自国", "普通话", "low",    "搞笑", ""),
    ("张永康", "脏永康", "普通话", "medium", "搞笑", "「张」+前鼻音字易出现"),

    # ===== 单字常见谐音雷区 =====
    ("史", "屎",   "普通话", "medium", "不雅", "「史」做名末字时风险大"),
    ("殷", "阴",   "普通话", "low",    "负面", "做姓时无碍，做名字时偶尔被嘲"),
    ("江", "僵",   "普通话", "low",    "负面", "搭配「死/僵」字时"),

    # ===== 粤语经典 =====
    ("有为",   "冇为",  "粤语",   "medium", "负面", "粤语中「有」「冇」音近"),
    ("贺",     "克",    "粤语",   "low",    "负面", ""),

    # ===== 吴语 =====
    ("树",     "输",    "吴语",   "low",    "负面", "上海/江浙地区"),

    # ===== 川渝 =====
    ("孙",     "酸",    "川渝",   "low",    "搞笑", "四川地区"),
]


# 索引（按首字 → 风险列表）
_INDEX: dict[str, list] = {}
for entry in HOMOPHONE_RISKS:
    pattern, sounds_like, lang, severity, category, note = entry
    for ch in pattern:
        _INDEX.setdefault(ch, []).append({
            "pattern": pattern,
            "sounds_like": sounds_like,
            "language": lang,
            "severity": severity,
            "category": category,
            "note": note,
        })


def check_homophone(full_name: str) -> list[dict]:
    """
    检测名字是否触发谐音风险。

    Args:
        full_name: 完整姓名，如 "张永康"

    Returns:
        命中的风险条目列表（按严重度倒序）
    """
    hits = []
    seen = set()
    # 检查全名包含的任意 pattern
    for pattern, sounds_like, lang, severity, category, note in HOMOPHONE_RISKS:
        # 完整匹配
        if pattern == full_name:
            key = (pattern, lang)
            if key not in seen:
                hits.append({
                    "pattern": pattern,
                    "sounds_like": sounds_like,
                    "language": lang,
                    "severity": severity,
                    "category": category,
                    "note": note,
                    "match_type": "exact",
                })
                seen.add(key)
        # 子串匹配（更宽松）
        elif len(pattern) >= 2 and pattern in full_name:
            key = (pattern, lang)
            if key not in seen:
                hits.append({
                    "pattern": pattern,
                    "sounds_like": sounds_like,
                    "language": lang,
                    "severity": severity,
                    "category": category,
                    "note": note,
                    "match_type": "substring",
                })
                seen.add(key)

    severity_order = {"high": 3, "medium": 2, "low": 1}
    hits.sort(key=lambda h: severity_order.get(h["severity"], 0), reverse=True)
    return hits


if __name__ == "__main__":
    print(f"✓ 谐音风险词库加载，共 {len(HOMOPHONE_RISKS)} 条")
    print()
    for name in ["张维城", "范统", "张永康", "杜子腾", "张敦翔", "张诗雯"]:
        risks = check_homophone(name)
        if risks:
            print(f"⚠️  {name}:")
            for r in risks:
                print(f"    [{r['severity']}] {r['language']}: 谐「{r['sounds_like']}」"
                      f" ({r['category']}) {r['note']}")
        else:
            print(f"✓ {name}: 无谐音风险")
