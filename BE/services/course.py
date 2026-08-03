"""
여행 코스 오케스트레이션.

PRD AI Workflow:
  사용자 입력 → TourAPI → Prompt 생성 → CLOVA Studio → 추천 결과 → Streamlit
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from BE.database import repository as repo
from BE.services import clova, maps, tourapi

logger = logging.getLogger(__name__)


def generate_course(
    location: str,
    purpose: str,
    time: str,
    transport: str,
    *,
    user_id: Optional[int] = None,
    save: bool = True,
    current_latitude: Optional[float] = None,
    current_longitude: Optional[float] = None,
) -> dict[str, Any]:
    """
    자연어 조건으로 여행 코스를 생성한다.

    Args:
        location: 현재 위치 / 지역
        purpose: 여행 목적 (자연어)
        time: 이용 가능 시간
        transport: 이동수단
        user_id: 저장 시 사용자 id (optional)
        save: True 이면 Course/History DB 저장 시도
        current_latitude/longitude: 지도 시작점 (optional)

    Returns:
        title, story, places, route, route_note, source, course_id, message?
    """
    logger.info(
        "generate_course location=%s time=%s transport=%s",
        location,
        time,
        transport,
    )

    query = {
        "location": location,
        "purpose": purpose,
        "time": time,
        "transport": transport,
    }

    # 1) TourAPI 후보
    try:
        candidates = tourapi.get_location(location, keyword=purpose, max_items=20)
    except Exception:
        logger.exception("TourAPI 실패")
        return {
            "title": None,
            "story": None,
            "places": [],
            "route": None,
            "route_note": None,
            "source": None,
            "course_id": None,
            "candidates_count": 0,
            "message": "관광 데이터 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        }

    if not candidates:
        return {
            "title": None,
            "story": None,
            "places": [],
            "route": None,
            "route_note": None,
            "source": None,
            "course_id": None,
            "candidates_count": 0,
            "message": "조건에 맞는 장소 후보를 찾지 못했습니다.",
        }

    # overview 가 비어 있으면 상위 후보만 detail 보강 (호출 수 제한)
    candidates = _enrich_overviews(candidates, limit=8)

    # 2) CLOVA 코스 생성 (내부에서 fallback 처리)
    course = clova.complete_course_json(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=candidates,
    )

    places = list(course.get("places") or [])
    if not places:
        return {
            "title": course.get("title"),
            "story": course.get("story"),
            "places": [],
            "route": None,
            "route_note": None,
            "source": course.get("source"),
            "course_id": None,
            "candidates_count": len(candidates),
            "message": "AI 코스 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        }

    # 3) 좌표 보강 (Maps geocode)
    places = maps.enrich_places_coordinates(places)

    current = None
    if current_latitude is not None and current_longitude is not None:
        current = {
            "latitude": float(current_latitude),
            "longitude": float(current_longitude),
        }

    route = maps.build_route_payload(places, current_location=current)

    result: dict[str, Any] = {
        "title": course.get("title"),
        "story": course.get("story"),
        "places": places,
        "route": route,
        "route_note": course.get("route_note"),
        "source": course.get("source", "clova"),
        "course_id": None,
        "candidates_count": len(candidates),
        "message": None,
    }

    # 4) DB 저장 (실패해도 추천 결과는 반환)
    if save:
        try:
            course_id = repo.save_course(
                title=str(result["title"] or "추천 코스"),
                story=result.get("story"),
                places=places,
                user_id=user_id,
                source=result.get("source"),
                query=query,
                result={
                    "title": result["title"],
                    "story": result["story"],
                    "places": places,
                    "route_note": result["route_note"],
                    "source": result["source"],
                },
            )
            result["course_id"] = course_id
        except Exception:
            logger.exception("코스 저장 실패 — 결과는 반환")

    return result


def _enrich_overviews(
    candidates: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    enriched = 0
    for c in candidates:
        item = dict(c)
        if not item.get("overview") and item.get("content_id") and enriched < limit:
            if not str(item["content_id"]).startswith("stub"):
                overview = tourapi.get_overview(
                    str(item["content_id"]),
                    item.get("content_type_id"),
                )
                if overview:
                    item["overview"] = overview[:500]
                    enriched += 1
        out.append(item)
    return out
