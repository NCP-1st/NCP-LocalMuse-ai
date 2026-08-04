"""CLOVA 여행 코스 프롬프트 템플릿 (JSON 출력 고정)."""

from __future__ import annotations

import json
from typing import Any

SYSTEM_CURATOR = (
    "당신은 한국 로컬 여행 큐레이터입니다. "
    "응답은 반드시 유효한 JSON 객체 하나만 출력합니다. "
    "마크다운 코드블록, 설명 문장, 주석을 절대 포함하지 마세요. "
    "후보 목록에 없는 장소를 새로 만들지 마세요. "
    "content_id 는 후보 값을 그대로 사용하세요."
)

SYSTEM_JSON_STRICT = (
    "Return exactly one valid JSON object and nothing else. "
    "No markdown fences, no explanations. "
    "Required keys: title (string), story (string), places (array length 3-5), route_note (string). "
    "Each place needs: name, category, address, latitude, longitude, duration, travel_time, reason, content_id. "
    "content_id must come from the candidate list."
)

COURSE_JSON_SCHEMA = """{
  "title": "코스 제목",
  "story": "지역 스토리 1~3문장",
  "places": [
    {
      "name": "장소명",
      "category": "카테고리",
      "address": "주소",
      "latitude": 0.0,
      "longitude": 0.0,
      "duration": "체류 시간",
      "travel_time": "이전 지점에서의 이동 시간",
      "reason": "추천 이유",
      "content_id": "후보 content_id"
    }
  ],
  "route_note": "동선 한 줄 요약"
}"""


def build_course_user_prompt(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
    place_count_hint: str = "3~5",
) -> str:
    candidate_json = json.dumps(candidates, ensure_ascii=False, indent=2)
    return f"""사용자의 현재 위치와 관광 데이터를 참고하여 정확히 {place_count_hint}개의 장소를 추천하세요.

규칙:
1. 후보는 아래 [후보 장소] 목록에서만 고르세요. content_id 를 그대로 복사하세요.
2. 방문 순서는 {transport} 이동 기준으로 동선이 자연스럽게 이어지게 하세요.
3. 카테고리를 가능하면 다양하게 섞으세요 (카페/산책/문화/식사 등).
4. 각 reason 은 1~2문장으로, 사용자 목적("{purpose}")과 지금 이 일정을 연결하세요.
5. story 는 {location} 지역 맥락 1~3문장.
6. duration / travel_time 은 한국어 짧은 표기 (예: "40분", "도보 12분").
7. 총 일정 시간({time})에 맞게 체류 시간을 배분하세요.
8. JSON 외 텍스트·코드블록 금지.

[사용자 조건]
- 위치: {location}
- 목적: {purpose}
- 시간: {time}
- 이동수단: {transport}

[후보 장소 — TourAPI]
{candidate_json}

[출력 JSON 스키마 — 이 형식만 출력]
{COURSE_JSON_SCHEMA}
"""


def build_strict_retry_suffix() -> str:
    return (
        "\n\nCRITICAL RETRY: Output ONLY the JSON object. "
        "places length MUST be between 3 and 5. "
        "Every content_id MUST exist in the candidate list above."
    )
