"""API 端点集成测试"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "name" in r.json()


def test_bazi_baby_male(client):
    r = client.post("/api/bazi", json={
        "year": 2023, "month": 1, "day": 14,
        "hour": 11, "minute": 33,
        "is_lunar": False, "gender": "男",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["day_master"] == "壬"
    assert data["day_master_wuxing"] == "水"
    assert data["naming_wuxing"]["primary"] == "火"
    assert "水" in data["naming_wuxing"]["avoid"]


def test_bazi_invalid_date(client):
    r = client.post("/api/bazi", json={
        "year": 2023, "month": 13, "day": 1,
        "hour": 0, "is_lunar": False, "gender": "男"
    })
    assert r.status_code == 422  # pydantic validation


def test_generate_male(client):
    r = client.post("/api/generate", json={
        "surname": "张",
        "gender": "男",
        "year": 2023, "month": 1, "day": 14,
        "hour": 11, "minute": 33,
        "top_n": 5,
    })
    assert r.status_code == 200
    data = r.json()
    assert "candidates" in data
    assert len(data["candidates"]) <= 5
    if data["candidates"]:
        first = data["candidates"][0]
        assert first["full_name"].startswith("张")
        assert "scores" in first
        assert "total_score" in first


def test_generate_with_must_include(client):
    r = client.post("/api/generate", json={
        "surname": "张",
        "gender": "女",
        "year": 2026, "month": 5, "day": 25,
        "hour": 14, "minute": 30,
        "must_include": "雯",
        "must_include_position": "second",
        "top_n": 5,
    })
    assert r.status_code == 200
    data = r.json()
    for c in data["candidates"]:
        assert "雯" in c["given_chars"]


def test_score_specific_name(client):
    r = client.post("/api/score", json={
        "surname": "张",
        "given_chars": ["维", "城"],
        "gender": "男",
        "year": 2023, "month": 1, "day": 14,
        "hour": 11, "minute": 33,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["full_name"] == "张维城"
    assert 0 <= data["total_score"] <= 100
    assert "bazi" in data["scores"]


def test_character_query(client):
    r = client.get("/api/character/雯")
    assert r.status_code == 200
    data = r.json()
    assert data["char"] == "雯"
    assert data["kangxi"] == 12
    assert data["wuxing"] == "水"


def test_character_not_found(client):
    r = client.get("/api/character/穒")  # 极冷僻字
    assert r.status_code == 404


def test_invalid_surname(client):
    r = client.post("/api/generate", json={
        "surname": "穒",
        "gender": "男",
        "year": 2023, "month": 1, "day": 14,
        "hour": 12,
    })
    assert r.status_code == 400
