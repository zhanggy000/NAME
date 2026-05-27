"""API 路由实现"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import queue
import sys
import threading
from pathlib import Path

# 确保可以 import 种子数据
_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "data" / "seed"))

from app.core.character_repo import get_char  # noqa: E402
from app.core.refs_repo import get_classics_for_char, get_famous_for_char  # noqa: E402
from app.core.bazi import compute_bazi, get_naming_wuxing  # noqa: E402
from app.core.scoring import score_name  # noqa: E402
from app.core.generator import generate_names, GenerateRequest  # noqa: E402
from app.services.llm_review import review_candidates_with_metadata  # noqa: E402
from app.services.cache import get_json, make_cache_key, set_json  # noqa: E402
from app.api.schemas import (
    BaziRequest, BaziResponse,
    GenerateNameRequest, GenerateNameResponse,
    AiReviewRequest, AiReviewResponse,
    ScoreRequest, ScoreResponse,
    CharacterDetail,
)


router = APIRouter(prefix="/api", tags=["naming"])


@router.post("/bazi", response_model=BaziResponse)
def api_bazi(req: BaziRequest):
    """排八字 + 求用神"""
    try:
        bz = compute_bazi(
            req.year, req.month, req.day, req.hour, req.minute,
            is_lunar=req.is_lunar, gender=req.gender,
        )
    except Exception as e:
        raise HTTPException(400, f"八字排盘失败: {e}")

    naming_wx = get_naming_wuxing(bz)
    return BaziResponse(
        bazi_string=bz.bazi_string,
        year_gz=f"{bz.year_gan}{bz.year_zhi}",
        month_gz=f"{bz.month_gan}{bz.month_zhi}",
        day_gz=f"{bz.day_gan}{bz.day_zhi}",
        hour_gz=f"{bz.hour_gan}{bz.hour_zhi}",
        day_master=bz.day_master,
        day_master_wuxing=bz.day_master_wuxing,
        month_name=bz.month_name,
        wuxing_count=bz.wuxing_count,
        wuxing_score=bz.wuxing_score,
        naming_wuxing=naming_wx,
    )


@router.post("/generate", response_model=GenerateNameResponse)
def api_generate(req: GenerateNameRequest):
    """生成名字 Top N"""
    cache_key = make_cache_key("generate", req.model_dump(mode="json"))
    cached = get_json(cache_key)
    if cached is not None and cached.get("trace"):
        return GenerateNameResponse(**cached)

    try:
        gr = GenerateRequest(
            surname=req.surname,
            gender=req.gender,
            year=req.year, month=req.month, day=req.day,
            hour=req.hour, minute=req.minute,
            is_lunar=req.is_lunar,
            must_include=req.must_include,
            must_include_position=req.must_include_position,
            must_avoid=req.must_avoid,
            style_prefs=req.style_prefs,
            weights=req.weights.model_dump() if req.weights else None,
            llm_config={
                "enabled": False,
                "provider": req.llm_provider or "deepseek",
                "api_key": "",
                "model": req.llm_model or "",
                "base_url": req.llm_base_url or "",
            },
            name_length=req.name_length,
            top_n=req.top_n,
        )
        result = generate_names(gr)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"生成失败: {e}")

    set_json(cache_key, result, ttl_seconds=3600)
    return GenerateNameResponse(**result)


@router.post("/generate/stream")
def api_generate_stream(req: GenerateNameRequest):
    """流式生成名字：边执行边输出中文日志，最后返回完整结果。"""
    def make_generate_request() -> GenerateRequest:
        return GenerateRequest(
            surname=req.surname,
            gender=req.gender,
            year=req.year, month=req.month, day=req.day,
            hour=req.hour, minute=req.minute,
            is_lunar=req.is_lunar,
            must_include=req.must_include,
            must_include_position=req.must_include_position,
            must_avoid=req.must_avoid,
            style_prefs=req.style_prefs,
            weights=req.weights.model_dump() if req.weights else None,
            llm_config={
                "enabled": False,
                "provider": req.llm_provider or "deepseek",
                "api_key": "",
                "model": req.llm_model or "",
                "base_url": req.llm_base_url or "",
            },
            name_length=req.name_length,
            top_n=req.top_n,
        )

    def sse(event: str, data: dict) -> str:
        payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"

    def event_stream():
        events: queue.Queue[tuple[str, dict]] = queue.Queue()

        def log(message: str) -> None:
            events.put(("log", {"message": message}))

        def run() -> None:
            try:
                result = generate_names(make_generate_request(), trace_callback=log)
                events.put(("result", result))
            except ValueError as exc:
                events.put(("error", {"message": str(exc)}))
            except Exception as exc:  # pragma: no cover - defensive streaming guard
                events.put(("error", {"message": f"生成失败: {exc}"}))
            finally:
                events.put(("done", {}))

        threading.Thread(target=run, daemon=True).start()
        yield sse("log", {"message": "连接成功：浏览器已打开实时日志通道。"})

        while True:
            event, data = events.get()
            yield sse(event, data)
            if event == "done":
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ai-review", response_model=AiReviewResponse)
def api_ai_review(req: AiReviewRequest):
    """用户主动点击后，才调用 AI 复核当前候选名单。"""
    if req.llm_provider == "none":
        raise HTTPException(400, "请选择一个 AI 供应商。")
    if not req.llm_api_key:
        raise HTTPException(400, "已选择 AI 复审，请先填写 API Key。")
    try:
        result = review_candidates_with_metadata(
            [c.model_dump(mode="json") for c in req.candidates],
            req.bazi,
            req.naming_wuxing,
            {
                "enabled": True,
                "provider": req.llm_provider or "deepseek",
                "api_key": req.llm_api_key or "",
                "model": req.llm_model or "",
                "base_url": req.llm_base_url or "",
            },
            max_count=req.max_count,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"AI 复审失败: {exc}")
    return AiReviewResponse(**result)


@router.post("/score", response_model=ScoreResponse)
def api_score(req: ScoreRequest):
    """给一个具体名字打分（用于父母对比候选）"""
    try:
        bz = compute_bazi(
            req.year, req.month, req.day, req.hour, req.minute,
            is_lunar=req.is_lunar, gender=req.gender,
        )
        naming_wx = get_naming_wuxing(bz)
        ns = score_name(
            req.surname, req.given_chars, naming_wx,
            gender=req.gender, style_prefs=req.style_prefs,
            weights=req.weights.model_dump() if req.weights else None,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"评分失败: {e}")

    d = ns.to_dict()
    return ScoreResponse(
        full_name=d["full_name"],
        total_score=d["total_score"],
        scores=d["scores"],
        wuge_result=d["wuge_result"],
        bazi=bz.to_dict(),
        naming_wuxing=naming_wx,
    )


@router.get("/character/{ch}", response_model=CharacterDetail)
def api_character(ch: str):
    """单字详情查询"""
    info = get_char(ch)
    if not info:
        raise HTTPException(404, f"字「{ch}」不在字库中")

    # 合并两个来源的典籍引用：
    #   1. characters_seed 的内联简版
    #   2. classics_corpus 全文反查
    inline_classics = info.get("classics_refs", [])
    corpus_hits = get_classics_for_char(ch)
    corpus_strs = [
        f"《{r['book']}·{r['chapter']}》{r['line']}"
        for r in corpus_hits
    ]
    all_classics = corpus_strs + [c for c in inline_classics
                                   if not any(c[:6] in cs for cs in corpus_strs)]

    # 名人引用合并
    inline_famous = info.get("famous_refs", [])
    corpus_famous = get_famous_for_char(ch, limit=10)
    corpus_famous_strs = [
        f"{f['full_name']}（{f['era']}{f['category']}）"
        for f in corpus_famous
    ]
    seen_names = {f.split("（")[0] for f in corpus_famous_strs}
    all_famous = corpus_famous_strs + [
        f for f in inline_famous
        if not any(name in f for name in seen_names)
    ]

    return CharacterDetail(
        char=info["char"],
        pinyin=info["pinyin"],
        tone=info["tone"],
        kangxi=info["kangxi"],
        simplified=info["simplified"],
        wuxing=info["wuxing"],
        radical=info.get("radical"),
        meaning=info["meaning"],
        gender_pref=info["gender_pref"],
        style_tags=info.get("style_tags", []),
        classics_refs=all_classics,
        famous_refs=all_famous,
    )
