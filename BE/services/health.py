"""시스템 헬스 체크 — 키 존재 여부 / DB ping (값은 노출하지 않음)."""

from __future__ import annotations

from typing import Any

from BE.database.connection import get_connection_info, ping
from BE.utils.config import get_settings


def get_health(*, probe: bool = False) -> dict[str, Any]:
    """
    Args:
        probe: True 이면 설정된 키로 가벼운 실호출 스모크를 시도한다.
               (키 값은 로그/응답에 포함하지 않음)
    """
    s = get_settings()
    db_info = get_connection_info()
    db_ok = ping()

    tour_ok = bool(s.tour_api_key)
    clova_ok = bool(s.clova_api_key)
    maps_ok = bool(
        (s.naver_map_client_id and s.naver_map_client_secret)
        or (s.naver_openapi_client_id and s.naver_openapi_client_secret)
    )

    services = [
        {
            "service": "TourAPI",
            "configured": tour_ok,
            "note": "한국관광공사 KorService1",
            "env": "TOUR_API_KEY",
        },
        {
            "service": "CLOVA Studio",
            "configured": clova_ok,
            "note": f"model={s.clova_model}",
            "env": "CLOVA_API_KEY",
        },
        {
            "service": "NAVER Maps",
            "configured": maps_ok,
            "note": "Geocoding / JS map (Client ID + Secret)",
            "env": "NAVER_MAP_CLIENT_ID / SECRET",
        },
        {
            "service": "Database",
            "configured": True,
            "note": f"kind={db_info['kind']} ok={db_ok}",
            "env": "DB_* or SQLITE_PATH",
        },
    ]

    probes: list[dict[str, Any]] = []
    if probe:
        probes = _run_probes(
            tour=tour_ok,
            clova=clova_ok,
            maps=maps_ok,
        )

    summary: list[str] = []
    missing = [
        x["service"]
        for x in services
        if not x["configured"] and x["service"] != "Database"
    ]
    if missing:
        summary.append(
            "미설정: "
            + ", ".join(missing)
            + " — ALLOW_STUB_WITHOUT_KEYS 로 스텁 동작 가능"
        )
    else:
        summary.append("주요 외부 API 키가 모두 설정되어 있습니다.")
    if db_ok:
        summary.append(f"DB 연결 정상 ({db_info['kind']}).")
    else:
        summary.append("DB ping 실패 — 경로/권한 확인 필요.")

    readiness = "ready" if not missing and db_ok else "partial" if db_ok else "blocked"
    if missing and s.allow_stub_without_keys:
        readiness = "demo_stub"

    return {
        "app_env": s.app_env,
        "default_region": s.default_region,
        "allow_stub": s.allow_stub_without_keys,
        "readiness": readiness,
        "db_ok": db_ok,
        "db": db_info,
        "services": services,
        "probes": probes,
        "summary": summary,
        "setup_hints": _setup_hints(missing),
    }


def _setup_hints(missing: list[str]) -> list[str]:
    hints = [
        "1) cp .env.example .env",
        "2) 공공데이터포털에서 TourAPI(KorService1) 인증키 발급 → TOUR_API_KEY",
        "3) NCP CLOVA Studio API Key → CLOVA_API_KEY",
        "4) NCP Maps Application Client ID/Secret → NAVER_MAP_CLIENT_ID/SECRET",
        "5) python -m BE health  또는  UI '시스템 상태' 페이지에서 확인",
    ]
    if not missing:
        return ["모든 키가 설정됨. python -m BE health --probe 로 실호출 스모크 가능"]
    return hints


def _run_probes(*, tour: bool, clova: bool, maps: bool) -> list[dict[str, Any]]:
    """키 값 없이 성공/실패만 반환."""
    results: list[dict[str, Any]] = []

    if tour:
        try:
            from BE.services import tourapi

            rows = tourapi.get_location("서울", keyword="공원", max_items=3)
            stub = bool(rows and str(rows[0].get("content_id", "")).startswith("stub"))
            results.append(
                {
                    "service": "TourAPI",
                    "ok": bool(rows) and not stub,
                    "detail": f"candidates={len(rows)}"
                    + (" (stub)" if stub else " (live)"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "service": "TourAPI",
                    "ok": False,
                    "detail": type(exc).__name__,
                }
            )
    else:
        results.append({"service": "TourAPI", "ok": False, "detail": "not configured"})

    if clova:
        try:
            from BE.services import clova as clova_svc

            # 실호출 대신 헤더/엔드포인트 구성 가능 여부 + 최소 후보로 complete
            # 네트워크 비용 있으므로 작은 후보만
            out = clova_svc.complete_course_json(
                location="성수",
                purpose="카페",
                time="2시간",
                transport="도보",
                candidates=[
                    {
                        "content_id": "probe-1",
                        "name": "테스트 카페",
                        "category": "음식점",
                        "address": "서울 성동구",
                        "latitude": 37.54,
                        "longitude": 127.05,
                        "overview": "probe",
                    }
                ],
            )
            results.append(
                {
                    "service": "CLOVA Studio",
                    "ok": out.get("source") == "clova",
                    "detail": f"source={out.get('source')}",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "service": "CLOVA Studio",
                    "ok": False,
                    "detail": type(exc).__name__,
                }
            )
    else:
        results.append(
            {"service": "CLOVA Studio", "ok": False, "detail": "not configured"}
        )

    if maps:
        try:
            from BE.services import maps as maps_svc

            coords = maps_svc.geocode("서울특별시 중구 세종대로 110")
            results.append(
                {
                    "service": "NAVER Maps",
                    "ok": coords is not None,
                    "detail": "geocode ok" if coords else "geocode empty/fail",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "service": "NAVER Maps",
                    "ok": False,
                    "detail": type(exc).__name__,
                }
            )
    else:
        results.append(
            {"service": "NAVER Maps", "ok": False, "detail": "not configured"}
        )

    return results
