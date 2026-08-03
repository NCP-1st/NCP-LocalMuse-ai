"""API 키 없이 스텁 파이프라인 스모크 테스트."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# 테스트용 격리 DB
os.environ["ALLOW_STUB_WITHOUT_KEYS"] = "true"
os.environ["TOUR_API_KEY"] = ""
os.environ["CLOVA_API_KEY"] = ""
os.environ["SQLITE_PATH"] = str(
    Path(__file__).resolve().parent / "_tmp_test_localmuse.sqlite3"
)

from BE.utils.config import clear_settings_cache  # noqa: E402

clear_settings_cache()

from BE.services.course import generate_course  # noqa: E402
from BE.services import clova  # noqa: E402
from BE.utils.json_extract import extract_json_object  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_generate_course_stub_flow():
    result = generate_course(
        location="성수",
        purpose="감성 카페와 산책",
        time="3시간",
        transport="도보",
        save=True,
    )
    assert result.get("message") in (None, "")
    assert result.get("title")
    assert len(result.get("places") or []) >= 3
    assert result.get("source") == "fallback"
    assert result.get("route") is not None
    assert result["route"]["available"] is True
    assert result.get("course_id") is not None


def test_fallback_diverse_categories():
    candidates = [
        {"name": "A", "category": "음식점", "overview": "a"},
        {"name": "B", "category": "음식점", "overview": "b"},
        {"name": "C", "category": "관광지", "overview": "c"},
        {"name": "D", "category": "문화시설", "overview": "d"},
    ]
    course = clova.fallback_course(
        location="성수",
        purpose="산책",
        time="2시간",
        transport="도보",
        candidates=candidates,
    )
    cats = [p["category"] for p in course["places"]]
    assert "관광지" in cats
    assert "문화시설" in cats


def test_normalize_merges_candidate_coords():
    raw = extract_json_object(
        '{"title":"T","story":"S","places":[{"name":"카페A","reason":"좋음","content_id":"1"}]}'
    )
    candidates = [
        {
            "content_id": "1",
            "name": "카페A",
            "address": "서울",
            "latitude": 37.5,
            "longitude": 127.0,
            "category": "음식점",
        }
    ]
    normalized = clova._normalize_course_json(raw, candidates=candidates)
    assert normalized["places"][0]["latitude"] == 37.5
