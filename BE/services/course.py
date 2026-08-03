"""
여행 코스 오케스트레이션.

PRD AI Workflow:
  사용자 입력 → TourAPI → Prompt 생성 → CLOVA Studio → 추천 결과 → Streamlit
"""

from __future__ import annotations

import logging
from typing import Any

from BE.services import clova, maps, tourapi

logger = logging.getLogger(__name__)


def generate_course(
    location: str,
    purpose: str,
    time: str,
    transport: str,
) -> dict[str, Any]:
    """
    자연어 조건으로 여행 코스를 생성한다.

    Args:
        location: 현재 위치 / 지역
        purpose: 여행 목적 (자연어)
        time: 이용 가능 시간
        transport: 이동수단

    Returns:
        title, story, places, route, route_note, message(optional)
    """
    logger.info(
        "generate_course location=%s time=%s transport=%s",
        location,
        time,
        transport,
    )

    try:
        candidates = tourapi.get_location(location, keyword=purpose)
    except Exception:
        logger.exception("TourAPI 실패")
        return {
            "title": None,
            "story": None,
            "places": [],
            "route": None,
            "message": "관광 데이터 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        }

    if not candidates:
        return {
            "title": None,
            "story": None,
            "places": [],
            "route": None,
            "message": "조건에 맞는 장소 후보를 찾지 못했습니다.",
        }

    try:
        course = clova.complete_course_json(
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
            candidates=candidates,
        )
    except Exception:
        logger.exception("CLOVA 실패 — fallback 경로 필요")
        return {
            "title": None,
            "story": None,
            "places": [],
            "route": None,
            "message": "AI 코스 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        }

    places = course.get("places") or []
    route = maps.build_route_payload(places)

    return {
        "title": course.get("title"),
        "story": course.get("story"),
        "places": places,
        "route": route,
        "route_note": course.get("route_note"),
        "source": course.get("source", "clova"),
    }
