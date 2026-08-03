from BE.utils.json_extract import extract_json_object


def test_plain_json():
    data = extract_json_object('{"title": "A", "places": []}')
    assert data["title"] == "A"


def test_fenced_json():
    text = """여기 결과입니다.
```json
{"title": "성수 코스", "places": [{"name": "카페"}]}
```
"""
    data = extract_json_object(text)
    assert data["title"] == "성수 코스"
    assert data["places"][0]["name"] == "카페"


def test_embedded_json_with_noise():
    text = '설명\n{"title": "X", "story": "Y"}\n끝'
    data = extract_json_object(text)
    assert data["story"] == "Y"
