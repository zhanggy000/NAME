"""Pydantic 请求/响应模型"""
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================
# /api/bazi
# ============================================================
class BaziRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    is_lunar: bool = False
    gender: Literal["男", "女"] = "男"


class BaziResponse(BaseModel):
    bazi_string: str
    year_gz: str
    month_gz: str
    day_gz: str
    hour_gz: str
    day_master: str
    day_master_wuxing: str
    month_name: str
    wuxing_count: dict
    wuxing_score: dict
    naming_wuxing: dict


# ============================================================
# /api/generate
# ============================================================
class GenerateNameRequest(BaseModel):
    # 基本信息
    surname: str = Field(..., min_length=1, max_length=2)
    gender: Literal["男", "女"] = "男"
    # 八字
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    is_lunar: bool = False
    # 偏好
    must_include: Optional[str] = Field(None, max_length=1)
    must_include_position: Optional[Literal["first", "second", "any"]] = "any"
    must_avoid: Optional[list[str]] = None
    style_prefs: Optional[list[str]] = None
    name_length: Literal[2] = 2
    top_n: int = Field(10, ge=1, le=50)


class DimensionScoreModel(BaseModel):
    name: str
    raw_score: float
    weighted_score: float
    breakdown: list


class CandidateName(BaseModel):
    full_name: str
    surname: str
    given_chars: list[str]
    total_score: float
    scores: dict
    wuge_result: dict


class GenerateNameResponse(BaseModel):
    bazi: dict
    naming_wuxing: dict
    candidates: list[CandidateName]
    stats: dict


# ============================================================
# /api/score
# ============================================================
class ScoreRequest(BaseModel):
    surname: str = Field(..., min_length=1, max_length=2)
    given_chars: list[str] = Field(..., min_length=1, max_length=2)
    gender: Literal["男", "女"] = "男"
    # 提供八字
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    is_lunar: bool = False
    style_prefs: Optional[list[str]] = None


class ScoreResponse(BaseModel):
    full_name: str
    total_score: float
    scores: dict
    wuge_result: dict
    bazi: dict
    naming_wuxing: dict


# ============================================================
# /api/character/{ch}
# ============================================================
class CharacterDetail(BaseModel):
    char: str
    pinyin: str
    tone: int
    kangxi: int
    simplified: int
    wuxing: str
    radical: Optional[str]
    meaning: str
    gender_pref: str
    style_tags: list[str]
    classics_refs: list[str]
    famous_refs: list[str]
