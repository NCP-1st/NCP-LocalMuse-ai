from BE.services import clova
from BE.services.course_quality import bind_to_candidates, finalize_course, parse_time_budget_minutes
from BE.utils.json_extract import extract_json_object


def test_parse_time_budget():
    assert parse_time_budget_minutes("3시간") == 180
    assert parse_time_budget_minutes("반나절") == 240
    assert parse_time_budget_minutes("90분") == 90


def test_bind_drops_hallucinated_places():
    candidates = [
        {
            "content_id": "1",
            "name": "성수 카페",
            "category": "음식점",
            "address": "성수",
            "latitude": 37.5,
            "longitude": 127.0,
        }
    ]
    places = [
        {"name": "존재하지않는장소", "content_id": "x", "reason": "fake"},
        {"name": "성수 카페", "content_id": "1", "reason": "좋음"},
    ]
    bound = bind_to_candidates(places, candidates)
    assert len(bound) == 1
    assert bound[0]["content_id"] == "1"


def test_finalize_pads_and_fills():
    candidates = [
        {
            "content_id": str(i),
            "name": f"P{i}",
            "category": cat,
            "address": "서울",
            "latitude": 37.5 + i * 0.01,
            "longitude": 127.0,
            "overview": "x",
        }
        for i, cat in enumerate(["음식점", "관광지", "문화시설", "음식점"])
    ]
    raw = {
        "title": "T",
        "story": "성수 지역 스토리입니다. 충분히 긴 설명.",
        "places": [{"name": "P0", "content_id": "0", "reason": "좋음"}],
    }
    out = finalize_course(
        raw,
        candidates=candidates,
        location="성수",
        purpose="카페",
        time="3시간",
        transport="도보",
    )
    assert len(out["places"]) >= 3
    assert out["places"][0]["duration"]
    assert out["quality"]["score"] >= 50


def test_ensure_place_count_compat():
    candidates = [
        {
            "content_id": str(i),
            "name": f"P{i}",
            "category": cat,
            "address": "서울",
            "latitude": 37.5,
            "longitude": 127.0,
            "overview": "x",
        }
        for i, cat in enumerate(["음식점", "관광지", "문화시설"])
    ]
    course = {
        "title": "T",
        "story": "스토리 문장입니다.",
        "places": [
            {
                "name": "P0",
                "content_id": "0",
                "category": "음식점",
                "latitude": 37.5,
                "longitude": 127.0,
            }
        ],
    }
    out = clova._ensure_place_count(
        course,
        candidates=candidates,
        location="성수",
        purpose="카페",
        time="3시간",
        transport="도보",
    )
    assert len(out["places"]) >= 3


def test_normalize_fuzzy_name():
    raw = {
        "title": "T",
        "story": "지역 스토리 충분히 길게 작성합니다.",
        "places": [{"name": "카페A 본점", "reason": "좋음"}],
    }
    candidates = [
        {
            "content_id": "9",
            "name": "카페A",
            "address": "성수",
            "latitude": 1.0,
            "longitude": 2.0,
            "category": "음식점",
        },
        {
            "content_id": "10",
            "name": "산책로",
            "address": "성수",
            "latitude": 1.1,
            "longitude": 2.1,
            "category": "관광지",
        },
        {
            "content_id": "11",
            "name": "전시관",
            "address": "성수",
            "latitude": 1.2,
            "longitude": 2.2,
            "category": "문화시설",
        },
    ]
    n = clova._normalize_course_json(raw, candidates=candidates)
    assert n["places"][0]["latitude"] == 1.0
    assert len(n["places"]) >= 3


def test_json_trailing_comma_and_fence():
    text = """```json
{"title": "A", "story": "hello story", "places": [{"name": "X"}],}
```"""
    data = extract_json_object(text)
    assert data["title"] == "A"
