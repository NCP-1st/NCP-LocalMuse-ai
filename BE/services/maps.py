"""
NAVER Maps 연동 — Dynamic Map(JS) 중심 (Geocode 비활성 기본).

전략 (유료/구독 차단 대응):
  - 좌표는 TourAPI mapx/mapy 를 1차 소스로 사용
  - Geocoding / Reverse Geocoding REST 는 기본 OFF
    (MAPS_USE_GEOCODE=true 이고 구독 가능할 때만 시도)
  - FE 는 Client ID + ncpKeyId 로 Dynamic Map Marker/Polyline 표시

지도 실패 시 FE는 텍스트 동선만 제공 (PRD Error Handling)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
REVERSE_GEOCODE_URL = (
    "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
)


class MapsError(RuntimeError):
    """NAVER Maps API 실패."""


def maps_use_geocode() -> bool:
    """Geocode REST 사용 여부. 기본 false (210 subscription 회피)."""
    raw = os.getenv("MAPS_USE_GEOCODE", "false").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def js_client_id() -> str | None:
    """Dynamic Map(JS) 용 Client ID (Secret 불필요)."""
    s = get_settings()
    return (s.naver_map_client_id or s.naver_openapi_client_id or "").strip() or None


def _map_credentials() -> tuple[str, str] | None:
    s = get_settings()
    client_id = (s.naver_map_client_id or s.naver_openapi_client_id or "").strip()
    client_secret = (
        s.naver_map_client_secret or s.naver_openapi_client_secret or ""
    ).strip()
    if not client_id or not client_secret:
        return None
    return client_id, client_secret


def _headers() -> dict[str, str]:
    creds = _map_credentials()
    if not creds:
        raise MapsError("NAVER Maps credentials not configured")
    client_id, client_secret = creds
    return {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
        "Accept": "application/json",
    }


def geocode(address: str) -> dict[str, float] | None:
    """
    주소 → {latitude, longitude}.
    MAPS_USE_GEOCODE=false 이면 호출하지 않음.
    """
    if not maps_use_geocode():
        return None
    if not address or not address.strip():
        return None
    if not _map_credentials():
        return None

    settings = get_settings()
    try:
        resp = requests.get(
            GEOCODE_URL,
            headers=_headers(),
            params={"query": address.strip()},
            timeout=settings.http_timeout_sec,
        )
        if resp.status_code >= 400:
            logger.info(
                "geocode skipped/failed HTTP %s (구독·권한 확인)",
                resp.status_code,
            )
            return None
        data = resp.json()
        addresses = data.get("addresses") or []
        if not addresses:
            return None
        first = addresses[0]
        return {
            "latitude": float(first["y"]),
            "longitude": float(first["x"]),
        }
    except Exception:
        logger.debug("geocode 실패: %s", address, exc_info=True)
        return None


def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """좌표 → 주소. MAPS_USE_GEOCODE=false 이면 호출하지 않음."""
    if not maps_use_geocode():
        return None
    if not _map_credentials():
        return None

    settings = get_settings()
    try:
        resp = requests.get(
            REVERSE_GEOCODE_URL,
            headers=_headers(),
            params={
                "coords": f"{longitude},{latitude}",
                "orders": "roadaddr,addr",
                "output": "json",
            },
            timeout=settings.http_timeout_sec,
        )
        if resp.status_code >= 400:
            logger.info(
                "reverse_geocode skipped/failed HTTP %s",
                resp.status_code,
            )
            return None
        data = resp.json()
        results = data.get("results") or []
        if not results:
            return None
        region = results[0].get("region") or {}
        land = results[0].get("land") or {}
        parts = [
            (region.get("area1") or {}).get("name"),
            (region.get("area2") or {}).get("name"),
            (region.get("area3") or {}).get("name"),
            land.get("name") or land.get("number1"),
        ]
        text = " ".join(p for p in parts if p)
        return text or None
    except Exception:
        logger.debug(
            "reverse_geocode 실패: %s,%s", latitude, longitude, exc_info=True
        )
        return None


def enrich_places_coordinates(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    좌표 정규화.
    - TourAPI 좌표 우선 유지
    - 좌표 없고 MAPS_USE_GEOCODE=true 일 때만 geocode 시도
    """
    enriched: list[dict[str, Any]] = []
    for p in places:
        item = dict(p)
        lat, lng = item.get("latitude"), item.get("longitude")
        # 문자열 좌표 정규화
        if lat is not None and lng is not None:
            try:
                item["latitude"] = float(lat)
                item["longitude"] = float(lng)
            except (TypeError, ValueError):
                item["latitude"] = None
                item["longitude"] = None
                lat, lng = None, None

        if (lat is None or lng is None) and item.get("address") and maps_use_geocode():
            coords = geocode(str(item["address"]))
            if coords:
                item["latitude"] = coords["latitude"]
                item["longitude"] = coords["longitude"]
                item["geocoded"] = True
        enriched.append(item)
    return enriched


def build_route_payload(
    places: list[dict[str, Any]],
    *,
    current_location: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    FE Dynamic Map 렌더링용 payload.

    render_hint:
      - naver_js : Client ID 있음 + 마커 있음 → NAVER Dynamic Map
      - st_map   : Client ID 없음 + 마커 있음 → Streamlit map 폴백
      - text     : 좌표 없음
    """
    markers: list[dict[str, Any]] = []
    polyline: list[list[float]] = []

    if (
        current_location
        and current_location.get("latitude") is not None
        and current_location.get("longitude") is not None
    ):
        polyline.append(
            [
                float(current_location["latitude"]),
                float(current_location["longitude"]),
            ]
        )

    for i, p in enumerate(places, start=1):
        lat = p.get("latitude")
        lng = p.get("longitude")
        if lat is None or lng is None:
            continue
        try:
            flat, flng = float(lat), float(lng)
        except (TypeError, ValueError):
            continue
        # 한국 대략 범위 가드 (잘못된 좌표 제외)
        if not (33.0 <= flat <= 39.5 and 124.0 <= flng <= 132.0):
            logger.debug("skip out-of-range coords %s,%s", flat, flng)
            continue
        markers.append(
            {
                "name": p.get("name", f"장소 {i}"),
                "lat": flat,
                "lng": flng,
                "order": i,
                "category": p.get("category") or "",
                "address": p.get("address") or "",
                "reason": p.get("reason") or "",
                "duration": p.get("duration") or "",
                "travel_time": p.get("travel_time") or "",
                "image": p.get("image") or "",
                "content_id": p.get("content_id") or "",
            }
        )
        polyline.append([flat, flng])

    available = bool(markers)
    client_id = js_client_id()
    if available and client_id:
        render_hint = "naver_js"
    elif available:
        render_hint = "st_map"
    else:
        render_hint = "text"

    return {
        "markers": markers,
        "polyline": polyline,
        "available": available,
        "current": current_location,
        "render_hint": render_hint,
        "marker_count": len(markers),
        "naver_client_id": client_id,
        "geocode_enabled": maps_use_geocode(),
        "coord_source": "tourapi_primary",
    }
