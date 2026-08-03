"""시스템 헬스 체크 — 키 존재 여부 / DB ping (값은 노출하지 않음)."""

from __future__ import annotations

from typing import Any

from BE.database.connection import get_connection_info, ping
from BE.utils.config import get_settings


def get_health() -> dict[str, Any]:
    s = get_settings()
    db_info = get_connection_info()
    db_ok = ping()

    services = [
        {
            "service": "TourAPI",
            "configured": bool(s.tour_api_key),
            "note": "한국관광공사 KorService1",
        },
        {
            "service": "CLOVA Studio",
            "configured": bool(s.clova_api_key),
            "note": f"model={s.clova_model}",
        },
        {
            "service": "NAVER Maps",
            "configured": bool(
                (s.naver_map_client_id and s.naver_map_client_secret)
                or (s.naver_openapi_client_id and s.naver_openapi_client_secret)
            ),
            "note": "Geocoding / JS map",
        },
        {
            "service": "Database",
            "configured": True,
            "note": f"kind={db_info['kind']} ok={db_ok}",
        },
    ]

    summary: list[str] = []
    missing = [x["service"] for x in services if not x["configured"] and x["service"] != "Database"]
    if missing:
        summary.append(
            "미설정: " + ", ".join(missing) + " — ALLOW_STUB_WITHOUT_KEYS 로 스텁 동작 가능"
        )
    else:
        summary.append("주요 외부 API 키가 모두 설정되어 있습니다.")
    if db_ok:
        summary.append(f"DB 연결 정상 ({db_info['kind']}).")
    else:
        summary.append("DB ping 실패 — 경로/권한 확인 필요.")

    return {
        "app_env": s.app_env,
        "default_region": s.default_region,
        "allow_stub": s.allow_stub_without_keys,
        "db_ok": db_ok,
        "db": db_info,
        "services": services,
        "summary": summary,
    }
