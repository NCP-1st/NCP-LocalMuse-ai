from BE.services import clova


def test_ensure_place_count_pads_to_three():
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
    course = {
        "title": "T",
        "story": "S",
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
        "story": "S",
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
        }
    ]
    n = clova._normalize_course_json(raw, candidates=candidates)
    assert n["places"][0]["latitude"] == 1.0
