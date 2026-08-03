"""
NAVER CLOVA Studio 연동.

역할 (PRD):
  - 여행 코스 생성
  - 추천 이유 생성
  - 지역 스토리 생성

컨벤션: Prompt 출력은 JSON 고정.
실패 시: Fallback Prompt (PRD Error Handling)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)


def generate_story(
    *,
    location: str,
    purpose: str,
    places: list[dict[str, Any]],
) -> str:
    """지역 스토리 / 코스 맥락 문단 생성."""
    result = complete_course_json(
        location=location,
        purpose=purpose,
        time="",
        transport="",
        candidates=places,
    )
    return str(result.get("story") or "")


def complete_course_json(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    CLOVA Studio에 코스 생성을 요청하고 JSON dict를 반환한다.

    실연동 전: 후보 기반 deterministic 스텁 JSON.
    """
    settings = get_settings()
    prompt = build_course_prompt(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=candidates,
    )

    if not settings.clova_api_key:
        logger.warning("CLOVA_API_KEY 미설정 — 스텁 코스 JSON 반환")
        return _fallback_course(
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
            candidates=candidates,
        )

    # TODO: CLOVA Studio Chat Completions 실연동
    logger.info("CLOVA 호출 예정 (prompt length=%d)", len(prompt))
    return _fallback_course(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=candidates,
    )


def build_course_prompt(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
) -> str:
    """여행 큐레이터 프롬프트 (JSON 출력 고정)."""
    candidate_json = json.dumps(candidates, ensure_ascii=False, indent=2)
    return f"""당신은 여행 큐레이터입니다.
사용자의 현재 위치와 관광 데이터를 참고하여 3~5개의 장소를 추천하세요.
반드시 JSON만 출력하세요.

[사용자 조건]
- 위치: {location}
- 목적: {purpose}
- 시간: {time}
- 이동수단: {transport}

[후보 장소 — TourAPI]
{candidate_json}

[출력 JSON 스키마]
{{
  "title": "코스 제목",
  "story": "지역 스토리 1~3문장",
  "places": [
    {{
      "name": "장소명",
      "category": "카테고리",
      "address": "주소",
      "latitude": 0.0,
      "longitude": 0.0,
      "duration": "체류 시간",
      "travel_time": "이전 지점에서의 이동 시간",
      "reason": "추천 이유"
    }}
  ],
  "route_note": "동선 한 줄 요약"
}}
"""


def _fallback_course(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """CLOVA 실패/미설정 시 Fallback (PRD)."""
    selected = candidates[:5] if candidates else []
    places = []
    for i, c in enumerate(selected):
        places.append(
            {
                "name": c.get("name", f"장소 {i + 1}"),
                "category": c.get("category", "-"),
                "address": c.get("address", ""),
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "duration": "40분",
                "travel_time": "도보 10분" if i else "출발",
                "reason": (
                    f"{c.get('overview') or c.get('name')} — "
                    f"'{purpose}' 요청과 {location} 일정({time}, {transport})에 맞춰 선정했습니다."
                ),
            }
        )

    return {
        "title": f"{location} {time} 로컬 코스",
        "story": (
            f"{location} 일대는 짧은 일정에도 카페·산책·문화 공간을 한 동선으로 "
            f"묶기 좋은 로컬 여행지입니다. ({transport} 이동 기준)"
        ),
        "places": places,
        "route_note": " → ".join(p["name"] for p in places) if places else "",
        "source": "fallback",
    }
