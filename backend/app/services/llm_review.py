"""
Claude LLM 复审与解释生成

职责（规则引擎做不了的）：
    1. 语感/时代感判断（古板？网红？土气？）
    2. 谐音风险（普通话+方言）
    3. 性别气质适配
    4. 整体韵味评估
    5. 为名字生成一段可读的 AI 复审意见

优先使用 DeepSeek API；若未配置则尝试 Anthropic；都不可用时自动降级为规则版理由（不影响打分）。
"""
from __future__ import annotations

import json
import logging
import os

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Claude SDK 懒导入（无 key 时不影响系统启动）
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


# ============================================================
# 系统提示（用 Prompt Caching 缓存这部分）
# ============================================================
AI_REVIEW_STANDARD = """AI 复审只做规则引擎不擅长的语感复核，不重新计算八字、三才五格，也不改动规则总分。
复审分为 0-10 分，按以下标准判断：
1. 语感顺口度 30%：连读是否自然，姓和名是否拗口，声母韵母是否别扭。
2. 谐音风险 25%：普通话为主，兼顾常见负面联想、歧义、玩笑化风险。
3. 时代感 15%：是否过时、网红化、用字堆砌，是否适合当代孩子长期使用。
4. 性别气质 10%：是否符合输入性别和名字整体气质，避免明显错位。
5. 文化契合 20%：在规则引擎给出的八字用神、字义、典籍信息基础上，判断表达是否统一。

评分约束：
- 8.5-10：语感优秀，风险低，文化表达统一。
- 7.0-8.4：整体可用，但有小的语感或辨识度问题。
- 5.0-6.9：能用但不推荐，存在明显短板。
- 5.0 以下：存在较大谐音、气质或使用风险。

音律复核硬约束：
- 候选名单里的 scores.phonetic 是规则引擎已经算出的音律读音分，phonetic_breakdown 是扣分细项；你不能忽略它。
- 如果 scores.phonetic 低于 65，必须优先复核连读、声母重复、韵母/鼻音尾过密、声调单调等问题。
- 如果低音律分确实对应拗口、重复或辨识度问题，issues 不能返回空数组；亮点里也要如实说明“意境好但读音有短板”。
- 不要因为字义、典籍或文化意境好，就掩盖明显的读音问题。
"""

SYSTEM_PROMPT = f"""你是资深的中文取名复审顾问。

{AI_REVIEW_STANDARD}

你的任务是为「已通过规则引擎初筛」的候选名字做最终复审，输出：
1. 0-10 分的 AI 复审分。
2. 该名字的「亮点/复审意见」，80-160 字。不要只写一句空泛好话，要说明语感是否顺口、寓意是否统一、时代感如何、是否推荐。
3. 「问题」清单，若没有明显问题则返回空数组。

输出格式严格为 JSON，不要任何额外说明。
"""


def is_llm_available() -> bool:
    """检测是否可调用 LLM"""
    return is_deepseek_available() or is_anthropic_available()


def is_deepseek_available(llm_config: dict | None = None) -> bool:
    if llm_config and not llm_config.get("enabled", False):
        return False
    if llm_config and llm_config.get("provider") == "none":
        return False
    key = (llm_config or {}).get("api_key") or settings.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
    provider = (llm_config or {}).get("provider") or settings.llm_provider
    return provider == "deepseek" and bool(key)


def is_anthropic_available(llm_config: dict | None = None) -> bool:
    if llm_config and not llm_config.get("enabled", False):
        return False
    if llm_config and llm_config.get("provider") == "none":
        return False
    key = (llm_config or {}).get("api_key") or settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
    provider = (llm_config or {}).get("provider") or settings.llm_provider
    return provider == "anthropic" and Anthropic is not None and bool(key)


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
            },
            "phonetic_breakdown": _negative_breakdown_reasons(c["scores"]["phonetic"]),
            "phonetic_review_hint": _phonetic_review_hint(c),
        })

    user_msg = f"""请复审以下候选名字。

【孩子信息】
- 八字：{bazi['bazi_string']}
- 日主：{bazi['day_master']}({bazi['day_master_wuxing']})
- 用神：{naming_wuxing['primary']}/{naming_wuxing['secondary']}

【候选名单】
{json.dumps(cand_brief, ensure_ascii=False, indent=2)}

请严格按系统消息里的五项 AI 复审标准判断。程序已经完成八字、五格、字义、音律、字形评分，你只需要做语感、谐音、时代感、性别气质、文化表达复核；不要重新计算八字或五格。
特别注意：如果 scores.phonetic 低于 65，必须结合 phonetic_breakdown 判断是否有连读拗口、声母重复、韵母/鼻音尾过密、声调单调等问题，并写入 issues。不要只写文化意境亮点。

请为每个名字输出复审结果。JSON 格式：
[
  {{
    "rank": 1,
    "name": "张XX",
    "llm_score": 8.5,
    "highlight": "请写 80-160 字复审意见：说明读音是否自然、字义和八字用神是否协调、时代感是否合适、有没有明显使用风险，最后给出是否推荐。",
    "issues": ["与某明星重名" 或 "声调略平"]
  }},
  ...
]
"""
    return user_msg


def build_review_messages(candidates: list[dict], bazi: dict, naming_wuxing: dict) -> dict:
    """Build the exact messages sent to the AI review model."""
    return {
        "system": SYSTEM_PROMPT,
        "user": _build_review_prompt(candidates, bazi, naming_wuxing),
    }


def review_candidates_with_metadata(
    candidates: list[dict],
    bazi: dict,
    naming_wuxing: dict,
    llm_config: dict,
    max_count: int = 100,
) -> dict:
    """Run AI review and return prompt, raw model text, and parsed reviews."""
    if not candidates:
        return {
            "prompt": build_review_messages([], bazi, naming_wuxing),
            "raw_response": "",
            "reviews": [],
            "candidates": [],
            "provider": llm_config.get("provider") or "deepseek",
            "model": llm_config.get("model") or "",
        }

    if not llm_config.get("enabled", False) or llm_config.get("provider") == "none":
        raise ValueError("请先启用 AI 复审。")
    if not llm_config.get("api_key"):
        raise ValueError("已选择 AI 复审，请先填写 API Key。")

    top = candidates[:max_count]
    messages = build_review_messages(top, bazi, naming_wuxing)
    provider = llm_config.get("provider") or "deepseek"

    if provider == "deepseek":
        metadata = _review_with_deepseek_metadata(top, bazi, naming_wuxing, llm_config, messages)
    elif provider == "anthropic":
        metadata = _review_with_anthropic_metadata(top, bazi, naming_wuxing, llm_config, messages)
    else:
        raise ValueError("不支持的 AI 供应商。")

    reviewed = _merge_reviews([dict(c) for c in top], metadata["reviews"])
    metadata["candidates"] = reviewed + candidates[max_count:]
    return metadata


def review_top_candidates(
    candidates: list[dict],
    bazi: dict,
    naming_wuxing: dict,
    max_count: int = 10,
    llm_config: dict | None = None,
    trace_callback=None,
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
    llm_config = llm_config or {}

    if not (is_deepseek_available(llm_config) or is_anthropic_available(llm_config)):
        _trace(trace_callback, "AI 复审未执行：当前没有可用模型配置，改用本地规则生成推荐摘要。")
        # 降级：规则版
        for c in top:
            c["llm_score"] = None
            c["highlight"] = _rule_based_highlight(c)
            c["issues"] = []
        return top + candidates[max_count:]

    _trace(trace_callback, "AI 复审标准：不重算八字五格，不改规则总分；只按语感30%、谐音25%、时代感15%、性别气质10%、文化契合20%复核。")

    # ===== DeepSeek 真实调用（优先）=====
    if is_deepseek_available(llm_config):
        try:
            return _review_with_deepseek(top, bazi, naming_wuxing, llm_config, trace_callback) + candidates[max_count:]
        except Exception as e:
            logger.warning(f"DeepSeek 复审失败，尝试其他 LLM 或规则降级: {e}")
            _trace(trace_callback, f"DeepSeek 复审失败：{_safe_error(e)}。准备检查是否可切换到其他模型。")

    if not is_anthropic_available(llm_config):
        _trace(trace_callback, "没有可切换的其他 AI 模型，本次语感复审降级为本地规则摘要。")
        for c in top:
            c["llm_score"] = None
            c["highlight"] = _rule_based_highlight(c)
            c["issues"] = []
        return top + candidates[max_count:]

    # ===== Anthropic 真实调用 =====
    try:
        model = llm_config.get("model") or settings.anthropic_model or os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")
        _trace(trace_callback, f"正在调用 Anthropic 模型：{model}，复审 Top {len(top)} 个名字。")
        client = Anthropic(api_key=(llm_config or {}).get("api_key") or settings.anthropic_api_key or None)
        msg = client.messages.create(
            model=model,
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
        reviews = _extract_json_array(msg.content[0].text.strip())
        _trace(trace_callback, f"Anthropic 已返回复审结果：解析到 {len(reviews)} 条评价。")
        return _merge_reviews(top, reviews, trace_callback) + candidates[max_count:]
    except Exception as e:
        logger.warning(f"LLM 复审失败，降级为规则版: {e}")
        _trace(trace_callback, f"AI 复审失败：{_safe_error(e)}。本次改用本地规则摘要。")
        for c in top:
            c["llm_score"] = None
            c["highlight"] = _rule_based_highlight(c)
            c["issues"] = []
        return top + candidates[max_count:]


def _extract_json_array(text: str) -> list[dict]:
    """Extract a JSON array from a chat model response."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end >= start:
        text = text[start:end + 1]
    return json.loads(text)


def _merge_reviews(top: list[dict], reviews: list[dict], trace_callback=None) -> list[dict]:
    """Merge model review output back into candidates."""
    rev_by_name = {r.get("name"): r for r in reviews}
    for c in top:
        rev = rev_by_name.get(c["full_name"])
        if rev:
            c["llm_score"] = rev.get("llm_score")
            c["highlight"] = rev.get("highlight", "")
            c["issues"] = _merge_phonetic_issues(c, rev.get("issues", []))
            issue_text = "；".join(c["issues"]) if c["issues"] else "暂无明显问题"
            _trace(
                trace_callback,
                f"AI 复审结果：{c['full_name']}，AI分 {c['llm_score']}，亮点：{c['highlight'] or '无'}，注意：{issue_text}。",
            )
        else:
            c["llm_score"] = None
            c["highlight"] = _rule_based_highlight(c)
            c["issues"] = _merge_phonetic_issues(c, [])
            _trace(trace_callback, f"AI 未返回「{c['full_name']}」的单独评价，已用本地规则摘要补齐。")
    return top


def _negative_breakdown_reasons(score: dict) -> list[str]:
    """Return concise negative scoring reasons for prompt context."""
    reasons = []
    for item in score.get("breakdown", []):
        if item.get("delta", 0) < 0:
            reason = item.get("reason")
            if reason:
                reasons.append(str(reason))
    return reasons


def _phonetic_review_hint(c: dict) -> str:
    phonetic = c["scores"]["phonetic"]
    raw = phonetic.get("raw_score", 0)
    reasons = _negative_breakdown_reasons(phonetic)
    if raw < 65:
        if reasons:
            return f"音律读音分偏低，必须重点复核：{'；'.join(reasons)}"
        return "音律读音分偏低，必须重点复核连读是否拗口。"
    return ""


def _merge_phonetic_issues(c: dict, issues: list[str] | None) -> list[str]:
    """Backfill obvious phonetic issues when the model omits them."""
    merged = [str(issue) for issue in (issues or []) if str(issue).strip()]
    phonetic = c["scores"]["phonetic"]
    raw = phonetic.get("raw_score", 0)
    if raw >= 65:
        return merged

    has_phonetic_issue = any(
        keyword in issue
        for issue in merged
        for keyword in ("读音", "音律", "拗口", "声母", "韵母", "声调", "连读", "鼻音")
    )
    if has_phonetic_issue:
        return merged

    reasons = _negative_breakdown_reasons(phonetic)
    if reasons:
        merged.append(f"音律读音分偏低：{'；'.join(reasons[:2])}")
    else:
        merged.append("音律读音分偏低，连读顺口度需谨慎")
    return merged


def _review_with_deepseek(
    top: list[dict],
    bazi: dict,
    naming_wuxing: dict,
    llm_config: dict | None = None,
    trace_callback=None,
) -> list[dict]:
    """Review candidates with DeepSeek's OpenAI-compatible chat endpoint."""
    llm_config = llm_config or {}
    api_key = llm_config.get("api_key") or settings.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
    base_url = (
        llm_config.get("base_url")
        or settings.deepseek_base_url
        or os.getenv("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    ).rstrip("/")
    model = llm_config.get("model") or settings.deepseek_model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    _trace(trace_callback, f"正在调用 DeepSeek 模型：{model}，接口地址：{base_url}，复审 Top {len(top)} 个名字。")

    messages = build_review_messages(top, bazi, naming_wuxing)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": messages["system"]},
            {"role": "user", "content": messages["user"]},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
    }

    with httpx.Client(timeout=45) as client:
        resp = client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        _trace(trace_callback, f"DeepSeek 已响应：HTTP {resp.status_code}。")
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = _extract_json_array(text)
    if isinstance(parsed, dict):
        reviews = parsed.get("reviews") or parsed.get("data") or parsed.get("items")
        if reviews is None and all(str(k).isdigit() for k in parsed.keys()):
            reviews = list(parsed.values())
    else:
        reviews = parsed
    if not isinstance(reviews, list):
        reviews = _extract_json_array(text)
    _trace(trace_callback, f"DeepSeek 复审完成：解析到 {len(reviews)} 条评价，准备合并到候选名字。")

    return _merge_reviews(top, reviews, trace_callback)


def _parse_review_text(text: str) -> list[dict]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = _extract_json_array(text)
    if isinstance(parsed, dict):
        reviews = parsed.get("reviews") or parsed.get("data") or parsed.get("items")
        if reviews is None and all(str(k).isdigit() for k in parsed.keys()):
            reviews = list(parsed.values())
    else:
        reviews = parsed
    if not isinstance(reviews, list):
        reviews = _extract_json_array(text)
    return reviews


def _review_with_deepseek_metadata(
    top: list[dict],
    bazi: dict,
    naming_wuxing: dict,
    llm_config: dict,
    messages: dict,
) -> dict:
    api_key = llm_config.get("api_key") or settings.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
    base_url = (
        llm_config.get("base_url")
        or settings.deepseek_base_url
        or os.getenv("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    ).rstrip("/")
    model = llm_config.get("model") or settings.deepseek_model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": messages["system"]},
            {"role": "user", "content": messages["user"]},
        ],
        "temperature": 0.2,
        "max_tokens": 4000,
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        raw_response = resp.json()["choices"][0]["message"]["content"]
    reviews = _parse_review_text(raw_response)
    return {
        "provider": "deepseek",
        "model": model,
        "prompt": messages,
        "raw_response": raw_response,
        "reviews": reviews,
    }


def _review_with_anthropic_metadata(
    top: list[dict],
    bazi: dict,
    naming_wuxing: dict,
    llm_config: dict,
    messages: dict,
) -> dict:
    if Anthropic is None:
        raise ValueError("Anthropic SDK 未安装，无法调用 Anthropic。")
    model = llm_config.get("model") or settings.anthropic_model or os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")
    client = Anthropic(api_key=llm_config.get("api_key") or settings.anthropic_api_key or None)
    msg = client.messages.create(
        model=model,
        max_tokens=4000,
        system=messages["system"],
        messages=[{"role": "user", "content": messages["user"]}],
    )
    raw_response = msg.content[0].text.strip()
    reviews = _parse_review_text(raw_response)
    return {
        "provider": "anthropic",
        "model": model,
        "prompt": messages,
        "raw_response": raw_response,
        "reviews": reviews,
    }


def _trace(trace_callback, message: str) -> None:
    if trace_callback:
        trace_callback(message)


def _safe_error(exc: Exception) -> str:
    text = str(exc)
    if len(text) > 240:
        text = text[:240] + "..."
    return text.replace("\n", " ")


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
