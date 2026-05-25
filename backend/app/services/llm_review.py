"""
Claude LLM 复审与解释生成

职责（规则引擎做不了的）：
    1. 语感/时代感判断（古板？网红？土气？）
    2. 谐音风险（普通话+方言）
    3. 性别气质适配
    4. 整体韵味评估
    5. 为每个 Top 名字生成「一句话推荐理由」

使用 Anthropic SDK + Prompt Caching 降低 80%+ 的 token 成本。
若 ANTHROPIC_API_KEY 未配置，自动降级为规则版理由（不影响打分）。
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Claude SDK 懒导入（无 key 时不影响系统启动）
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


# ============================================================
# 系统提示（用 Prompt Caching 缓存这部分）
# ============================================================
SYSTEM_PROMPT = """你是资深的中文取名顾问，精通：
- 中国传统命理（八字、五行、调候用神）
- 三才五格姓名学
- 中国古典文学（诗经、楚辞、唐诗、宋词、四书五经）
- 现代汉语语感、谐音、方言敏感性

你的任务是为「已通过规则引擎初筛」的候选名字做最终复审，输出：
1. 0-10 分的复审分（综合语感、时代感、性别气质、谐音、文化深度）
2. 该名字的「亮点」短句（10-30 字）
3. 「问题」清单（若有谐音/重名/过时/性别不符等）

输出格式严格为 JSON，不要任何额外说明。
"""


def is_llm_available() -> bool:
    """检测是否可调用 LLM"""
    return Anthropic is not None and bool(os.getenv("ANTHROPIC_API_KEY"))


def _build_review_prompt(candidates: list[dict], bazi: dict, naming_wuxing: dict) -> str:
    """构建复审请求"""
    cand_brief = []
    for i, c in enumerate(candidates, 1):
        cand_brief.append({
            "rank": i,
            "name": c["full_name"],
            "given_chars": c["given_chars"],
            "rule_score": c["total_score"],
            "scores": {
                "bazi": c["scores"]["bazi"]["raw_score"],
                "wuge": c["scores"]["wuge"]["raw_score"],
                "meaning": c["scores"]["meaning"]["raw_score"],
                "phonetic": c["scores"]["phonetic"]["raw_score"],
            }
        })

    user_msg = f"""请复审以下候选名字。

【孩子信息】
- 八字：{bazi['bazi_string']}
- 日主：{bazi['day_master']}({bazi['day_master_wuxing']})
- 用神：{naming_wuxing['primary']}/{naming_wuxing['secondary']}

【候选名单】
{json.dumps(cand_brief, ensure_ascii=False, indent=2)}

请为每个名字输出复审结果。JSON 格式：
[
  {{
    "rank": 1,
    "name": "张XX",
    "llm_score": 8.5,
    "highlight": "意境清远，典籍有据",
    "issues": ["与某明星重名" 或 "声调略平"]
  }},
  ...
]
"""
    return user_msg


def review_top_candidates(
    candidates: list[dict],
    bazi: dict,
    naming_wuxing: dict,
    max_count: int = 10,
) -> list[dict]:
    """
    对 Top N 候选做 LLM 复审。

    Returns:
        若 LLM 可用：每个候选增加 {"llm_score","highlight","issues"} 字段
        若不可用：每个候选用规则法生成简版理由
    """
    if not candidates:
        return candidates

    top = candidates[:max_count]

    if not is_llm_available():
        # 降级：规则版
        for c in top:
            c["llm_score"] = None
            c["highlight"] = _rule_based_highlight(c)
            c["issues"] = []
        return top + candidates[max_count:]

    # ===== LLM 真实调用 =====
    try:
        client = Anthropic()
        msg = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7"),
            max_tokens=2000,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # ← Prompt Caching
                }
            ],
            messages=[
                {"role": "user", "content": _build_review_prompt(top, bazi, naming_wuxing)}
            ],
        )
        text = msg.content[0].text.strip()
        # 提取 JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        reviews = json.loads(text)

        # 合并到候选
        rev_by_name = {r["name"]: r for r in reviews}
        for c in top:
            rev = rev_by_name.get(c["full_name"])
            if rev:
                c["llm_score"] = rev.get("llm_score")
                c["highlight"] = rev.get("highlight", "")
                c["issues"] = rev.get("issues", [])
            else:
                c["llm_score"] = None
                c["highlight"] = _rule_based_highlight(c)
                c["issues"] = []

        return top + candidates[max_count:]
    except Exception as e:
        logger.warning(f"LLM 复审失败，降级为规则版: {e}")
        for c in top:
            c["llm_score"] = None
            c["highlight"] = _rule_based_highlight(c)
            c["issues"] = []
        return top + candidates[max_count:]


def _rule_based_highlight(c: dict) -> str:
    """规则版亮点摘要"""
    parts = []
    ss = c["scores"]
    if ss["bazi"]["raw_score"] >= 90:
        parts.append("用神补益到位")
    if ss["wuge"]["raw_score"] >= 90:
        parts.append("五格全吉")
    if ss["meaning"]["raw_score"] >= 70:
        parts.append("字义典雅")

    # 检查典籍
    meaning_bd = ss["meaning"].get("breakdown", [])
    if any("典籍" in str(b.get("reason","")) for b in meaning_bd):
        parts.append("有典籍出处")
    if any("名人" in str(b.get("reason","")) for b in meaning_bd):
        parts.append("有名人参照")

    return "，".join(parts) if parts else "综合表现稳定"


if __name__ == "__main__":
    # 演示：模拟无 LLM 时的行为
    fake_candidates = [
        {
            "full_name": "张维城",
            "given_chars": ["维", "城"],
            "total_score": 85,
            "scores": {
                "bazi": {"raw_score": 88, "breakdown": []},
                "wuge": {"raw_score": 95, "breakdown": []},
                "meaning": {"raw_score": 75,
                           "breakdown": [{"reason":"典籍《诗经》"}]},
                "phonetic": {"raw_score": 80, "breakdown": []},
            }
        }
    ]
    print(f"LLM available: {is_llm_available()}")
    result = review_top_candidates(fake_candidates, {"bazi_string":"...","day_master":"壬","day_master_wuxing":"水"}, {"primary":"火","secondary":"土"})
    print(json.dumps(result, ensure_ascii=False, indent=2))
