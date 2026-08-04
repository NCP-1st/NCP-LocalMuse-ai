"""시스템 헬스 체크 — 키 존재 여부 / DB ping / 실호출 probe (값은 노출하지 않음)."""

from __future__ import annotations

from typing import Any

from BE.database.connection import get_connection_info, ping
from BE.utils.config import get_settings


def get_health(*, probe: bool = False) -> dict[str, Any]:
    """
    Args:
        probe: True 이면 설정된 키로 가벼운 실호출 스모크를 시도한다.
    """
    s = get_settings()
    db_info = get_connection_info()
    db_ok = ping()

    tour_ok = bool(s.tour_api_key)
    clova_ok = bool(s.clova_api_key)
    maps_js_ok = bool(s.naver_map_client_id or s.naver_openapi_client_id)
    maps_geo_ok = bool(
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
            "service": "NAVER Maps JS",
            "configured": maps_js_ok,
            "note": "Dynamic Map (ncpKeyId) — Marker/Polyline",
            "env": "NAVER_MAP_CLIENT_ID",
        },
        {
            "service": "NAVER Maps Geocode",
            "configured": maps_geo_ok,
            "note": "선택(기본 OFF). MAPS_USE_GEOCODE=true 일 때만 호출",
            "env": "MAPS_USE_GEOCODE + CLIENT_ID/SECRET",
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
            maps_geo=maps_geo_ok,
            maps_js=maps_js_ok,
        )

    summary: list[str] = []
    missing = [
        x["service"]
        for x in services
        if not x["configured"] and x["service"] != "Database"
    ]
    # 데모 최소: Tour + CLOVA (+ Maps JS 권장)
    core_missing = [
        m
        for m in missing
        if m in {"TourAPI", "CLOVA Studio"}
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

    if not core_missing and maps_js_ok and db_ok:
        readiness = "ready"
    elif not core_missing and db_ok:
        readiness = "ready_no_map_js"  # geocode/js partial
    elif missing and s.allow_stub_without_keys:
        readiness = "demo_stub"
    elif db_ok:
        readiness = "partial"
    else:
        readiness = "blocked"

    # probe 결과로 live_ready 보정
    live_bits = {
        "tour": False,
        "clova": False,
        "maps_geo": False,
    }
    for p in probes:
        if p.get("service") == "TourAPI":
            live_bits["tour"] = bool(p.get("ok"))
        elif p.get("service") == "CLOVA Studio":
            live_bits["clova"] = bool(p.get("ok"))
        elif p.get("service") == "NAVER Maps Geocode":
            live_bits["maps_geo"] = bool(p.get("ok"))

    return {
        "app_env": s.app_env,
        "default_region": s.default_region,
        "allow_stub": s.allow_stub_without_keys,
        "readiness": readiness,
        "live_bits": live_bits if probe else None,
        "db_ok": db_ok,
        "db": db_info,
        "services": services,
        "probes": probes,
        "summary": summary,
        "setup_hints": _setup_hints(missing),
    }


def _setup_hints(missing: list[str]) -> list[str]:
    if not missing:
        return [
            "모든 키가 설정됨.",
            "python -m BE health --probe",
            "python -m BE e2e   # 성수 PRD 시나리오 E2E",
        ]
    return [
        "1) cp .env.example .env",
        "2) data.go.kr → TourAPI(KorService1) 인증키 → TOUR_API_KEY",
        "3) NCP CLOVA Studio API Key → CLOVA_API_KEY",
        "4) NCP Maps Application → NAVER_MAP_CLIENT_ID (+ SECRET for Geocode)",
        "5) python -m BE health --probe",
        "6) python -m BE e2e",
        "누락: " + ", ".join(missing),
    ]


def _run_probes(
    *,
    tour: bool,
    clova: bool,
    maps_geo: bool,
    maps_js: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # TourAPI
    if tour:
        try:
            from BE.services import tourapi

            rows = tourapi.get_location("성수", keyword="카페", max_items=5)
            stub = bool(
                rows and str(rows[0].get("content_id", "")).startswith("stub")
            )
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
        results.append(
            {"service": "TourAPI", "ok": False, "detail": "not configured"}
        )

    # CLOVA — 짧은 후보로 실호출
    if clova:
        try:
            from BE.services import clova as clova_svc

            out = clova_svc.complete_course_json(
                location="성수",
                purpose="카페와 산책",
                time="2시간",
                transport="도보",
                candidates=[
                    {
                        "content_id": "probe-1",
                        "name": "성수 카페 테스트",
                        "category": "음식점",
                        "address": "서울 성동구 성수동",
                        "latitude": 37.5446,
                        "longitude": 127.0557,
                        "overview": "probe candidate",
                    },
                    {
                        "content_id": "probe-2",
                        "name": "성수 산책로 테스트",
                        "category": "관광지",
                        "address": "서울 성동구 성수동",
                        "latitude": 37.5470,
                        "longitude": 127.0600,
                        "overview": "probe walk",
                    },
                    {
                        "content_id": "probe-3",
                        "name": "성수 문화공간 테스트",
                        "category": "문화시설",
                        "address": "서울 성동구 성수동",
                        "latitude": 37.5410,
                        "longitude": 127.0520,
                        "overview": "probe culture",
                    },
                ],
            )
            results.append(
                {
                    "service": "CLOVA Studio",
                    "ok": out.get("source") == "clova",
                    "detail": f"source={out.get('source')} places={len(out.get('places') or [])}",
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

    # Maps Geocode — 기본 비활성 (유료/구독 210 회피)
    from BE.services.maps import maps_use_geocode

    if not maps_use_geocode():
        results.append(
            {
                "service": "NAVER Maps Geocode",
                "ok": True,
                "detail": "disabled (TourAPI coords + Dynamic Map only)",
            }
        )
    elif maps_geo:
        try:
            from BE.services import maps as maps_svc

            coords = maps_svc.geocode("서울특별시 성동구 성수동")
            results.append(
                {
                    "service": "NAVER Maps Geocode",
                    "ok": coords is not None,
                    "detail": "geocode ok" if coords else "geocode empty/fail (210?)",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "service": "NAVER Maps Geocode",
                    "ok": False,
                    "detail": type(exc).__name__,
                }
            )
    else:
        results.append(
            {
                "service": "NAVER Maps Geocode",
                "ok": False,
                "detail": "not configured",
            }
        )

    # Maps JS — Client ID (Dynamic Map)
    results.append(
        {
            "service": "NAVER Maps JS",
            "ok": maps_js,
            "detail": (
                "client_id set — Web URL: http://localhost (no port)"
                if maps_js
                else "not configured"
            ),
        }
    )

    return results
