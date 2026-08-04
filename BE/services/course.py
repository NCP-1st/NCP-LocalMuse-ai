"""
여행 코스 오케스트레이션.

PRD AI Workflow:
  사용자 입력 → TourAPI → Prompt 생성 → CLOVA Studio → 추천 결과 → Streamlit
"""

from __future__ import annotations

import logging
import time as time_mod
from collections.abc import Callable
from typing import Any, Optional

from BE.database import repository as repo
from BE.services import clova, maps, tourapi

logger = logging.getLogger(__name__)

StageCallback = Callable[[str, dict[str, Any]], None]


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
    on_stage: StageCallback | None = None,
) -> dict[str, Any]:
    """
    자연어 조건으로 여행 코스를 생성한다.

    on_stage(stage_name, payload): 진행 단계 콜백
      - tourapi | clova | maps | save | done
    """
    logger.info(
        "generate_course location=%s time=%s transport=%s",
        location,
        time,
        transport,
    )

    stages: list[dict[str, Any]] = []
    t0 = time_mod.perf_counter()

    def emit(name: str, **payload: Any) -> None:
        item = {"stage": name, **payload}
        stages.append(item)
        if on_stage:
            try:
                on_stage(name, payload)
            except Exception:
                logger.exception("on_stage callback error")

    query = {
        "location": location,
        "purpose": purpose,
        "time": time,
        "transport": transport,
    }

    # 1) TourAPI 후보
    emit("tourapi", status="start", message="관광 데이터 조회 중…")
    try:
        candidates = tourapi.get_location(location, keyword=purpose, max_items=20)
    except Exception:
        logger.exception("TourAPI 실패")
        emit("tourapi", status="error", message="TourAPI 실패")
        return _error_result(
            "관광 데이터 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.",
            stages=stages,
            t0=t0,
        )

    if not candidates:
        emit("tourapi", status="empty", message="후보 없음")
        return _error_result(
            "조건에 맞는 장소 후보를 찾지 못했습니다.",
            stages=stages,
            t0=t0,
        )

    emit(
        "tourapi",
        status="ok",
        message=f"후보 {len(candidates)}곳",
        count=len(candidates),
    )

    # overview 보강
    candidates = _enrich_overviews(candidates, limit=8)

    # 2) CLOVA 코스 생성
    emit("clova", status="start", message="AI 코스·추천 이유 생성 중…")
    course = clova.complete_course_json(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=candidates,
    )

    places = list(course.get("places") or [])
    if not places:
        emit("clova", status="error", message="빈 코스")
        return _error_result(
            "AI 코스 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.",
            stages=stages,
            t0=t0,
            source=course.get("source"),
            candidates_count=len(candidates),
        )

    emit(
        "clova",
        status="ok",
        message=f"source={course.get('source')}, places={len(places)}",
        source=course.get("source"),
        place_count=len(places),
    )

    # 3) 좌표 보강 + route
    emit("maps", status="start", message="좌표·동선 구성 중…")
    places = maps.enrich_places_coordinates(places)

    current = None
    if current_latitude is not None and current_longitude is not None:
        current = {
            "latitude": float(current_latitude),
            "longitude": float(current_longitude),
        }

    route = maps.build_route_payload(places, current_location=current)
    emit(
        "maps",
        status="ok" if route.get("available") else "partial",
        message="지도 동선 준비 완료" if route.get("available") else "좌표 부족 — 텍스트 동선",
        available=bool(route.get("available")),
        markers=len(route.get("markers") or []),
    )

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
        "fallback_note": course.get("fallback_note"),
        "quality": course.get("quality"),
        "attempt": course.get("attempt"),
        "retry": course.get("retry"),
        "stages": stages,
        "elapsed_ms": None,
    }

    # 4) DB 저장
    if save:
        emit("save", status="start", message="코스 저장 중…")
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
            emit("save", status="ok", message=f"course_id={course_id}", course_id=course_id)
        except Exception:
            logger.exception("코스 저장 실패 — 결과는 반환")
            emit("save", status="error", message="저장 실패 (결과는 표시)")

    result["elapsed_ms"] = int((time_mod.perf_counter() - t0) * 1000)
    emit("done", status="ok", message="완료", elapsed_ms=result["elapsed_ms"])
    return result


def _error_result(
    message: str,
    *,
    stages: list[dict[str, Any]],
    t0: float,
    source: str | None = None,
    candidates_count: int = 0,
) -> dict[str, Any]:
    return {
        "title": None,
        "story": None,
        "places": [],
        "route": None,
        "route_note": None,
        "source": source,
        "course_id": None,
        "candidates_count": candidates_count,
        "message": message,
        "stages": stages,
        "elapsed_ms": int((time_mod.perf_counter() - t0) * 1000),
    }


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
