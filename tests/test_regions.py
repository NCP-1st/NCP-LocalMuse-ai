from BE.utils.regions import extract_search_keyword, resolve_area_code


def test_seoul_area():
    assert resolve_area_code("서울") == 1
    assert resolve_area_code("성수") == 1
    assert resolve_area_code("부산 해운대") == 6


def test_search_keyword_from_purpose():
    kw = extract_search_keyword(
        "성수",
        "성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.",
    )
    assert "성수" in kw or "감성" in kw or "카페" in kw
