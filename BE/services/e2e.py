"""
PRD 데모 E2E — 성수 3시간 감성 카페+산책.

키 값은 절대 출력하지 않는다.
실데이터 여부(live/stub)와 지도 준비 상태만 요약한다.
"""

from __future__ import annotations

from typing import Any

from BE.services.course import generate_course
from BE.services.health import get_health
from BE.utils.config import get_settings

# PRD Demo Scenario
SEONGSU_LOCATION = "성수"
SEONGSU_PURPOSE = "성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘."
SEONGSU_TIME = "3시간"
SEONGSU_TRANSPORT = "도보"


def run_seongsu_e2e(*, save: bool = False, probe: bool = True) -> dict[str, Any]:
    """
    1) health(+probe)
    2) generate_course 성수 시나리오
    3) live/stub · 지도 판정
    """
    settings = get_settings()
    health = get_health(probe=probe)

    stages: list[dict[str, Any]] = []

    def on_stage(name: str, payload: dict[str, Any]) -> None:
        stages.append({"stage": name, **payload})

    result = generate_course(
        location=SEONGSU_LOCATION,
        purpose=SEONGSU_PURPOSE,
        time=SEONGSU_TIME,
        transport=SEONGSU_TRANSPORT,
        save=save,
        on_stage=on_stage,
    )

    places = result.get("places") or []
    route = result.get("route") or {}
    markers = route.get("markers") or []

    tour_live = _probe_ok(health, "TourAPI")
    clova_live = result.get("source") == "clova"
    maps_geocode_live = _probe_ok(health, "NAVER Maps Geocode") or _probe_ok(
        health, "NAVER Maps"
    )
    maps_js_ready = bool(
        settings.naver_map_client_id or settings.naver_openapi_client_id
    )

    # 후보가 stub content_id 인지
    stub_places = sum(
        1
        for p in places
        if str(p.get("content_id") or "").startswith("stub")
    )
    places_look_live = len(places) > 0 and stub_places == 0 and tour_live

    map_render = "text"
    if route.get("available") and maps_js_ready:
        map_render = "naver_js"
    elif route.get("available"):
        map_render = "st_map"

    demo_ok = len(places) >= 3 and bool(result.get("title"))
    live_demo_ok = (
        demo_ok
        and clova_live
        and places_look_live
        and map_render in {"naver_js", "st_map"}
    )

    verdict = {
        "demo_ok": demo_ok,
        "live_demo_ok": live_demo_ok,
        "tour_live": tour_live and places_look_live,
        "clova_live": clova_live,
        "maps_js_ready": maps_js_ready,
        "maps_geocode_live": maps_geocode_live,
        "map_render": map_render,
        "route_available": bool(route.get("available")),
        "marker_count": len(markers),
        "message": _verdict_message(
            demo_ok=demo_ok,
            live_demo_ok=live_demo_ok,
            tour_live=tour_live and places_look_live,
            clova_live=clova_live,
            maps_js_ready=maps_js_ready,
            map_render=map_render,
        ),
    }

    return {
        "scenario": {
            "location": SEONGSU_LOCATION,
            "purpose": SEONGSU_PURPOSE,
            "time": SEONGSU_TIME,
            "transport": SEONGSU_TRANSPORT,
        },
        "health": {
            "readiness": health.get("readiness"),
            "services": health.get("services"),
            "probes": health.get("probes"),
            "summary": health.get("summary"),
        },
        "course": {
            "title": result.get("title"),
            "source": result.get("source"),
            "place_count": len(places),
            "candidates_count": result.get("candidates_count"),
            "quality": result.get("quality"),
            "elapsed_ms": result.get("elapsed_ms"),
            "route_available": bool(route.get("available")),
            "markers": len(markers),
            "route_note": result.get("route_note"),
            "places_preview": [
                {
                    "name": p.get("name"),
                    "category": p.get("category"),
                    "content_id": p.get("content_id"),
                    "has_coords": p.get("latitude") is not None
                    and p.get("longitude") is not None,
                }
                for p in places[:5]
            ],
            "fallback_note": result.get("fallback_note"),
        },
        "stages": stages,
        "verdict": verdict,
    }


def _probe_ok(health: dict[str, Any], service: str) -> bool:
    for p in health.get("probes") or []:
        if p.get("service") == service and p.get("ok"):
            return True
    return False


def _verdict_message(
    *,
    demo_ok: bool,
    live_demo_ok: bool,
    tour_live: bool,
    clova_live: bool,
    maps_js_ready: bool,
    map_render: str,
) -> str:
    if live_demo_ok:
        return (
            "PASS: 실데이터 데모 준비 완료 "
            f"(Tour live, CLOVA live, map={map_render})"
        )
    if demo_ok:
        missing = []
        if not tour_live:
            missing.append("TourAPI 실키/실데이터")
        if not clova_live:
            missing.append("CLOVA 실키(현재 fallback)")
        if map_render == "text":
            missing.append("지도 좌표")
        elif not maps_js_ready and map_render == "st_map":
            missing.append("NAVER_MAP_CLIENT_ID(JS 지도, 선택)")
        return "PARTIAL: 스텁/일부 연동으로 데모 가능 — 부족: " + ", ".join(
            missing or ["확인 필요"]
        )
    return "FAIL: 코스 생성 실패 — 로그/키 설정을 확인하세요."
