"""
NAVER Maps API 연동 (NCP Maps).

사용 기능 (PRD):
  - Geocoding (주소 → 좌표)
  - Reverse Geocoding (좌표 → 주소)
  - Marker / Polyline 데이터 구성
  - 현재 위치 표시 보조

지도 실패 시 FE는 텍스트 추천만 제공 (PRD Error Handling)
"""

from __future__ import annotations

import logging
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


def _map_credentials() -> tuple[str, str] | None:
    s = get_settings()
    client_id = s.naver_map_client_id or s.naver_openapi_client_id
    client_secret = s.naver_map_client_secret or s.naver_openapi_client_secret
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
    """주소 → {latitude, longitude}."""
    if not address or not address.strip():
        return None
    if not _map_credentials():
        logger.warning("NAVER Maps 키 미설정 — geocode skip")
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
            logger.warning("geocode HTTP %s: %s", resp.status_code, resp.text[:200])
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
        logger.exception("geocode 실패: %s", address)
        return None


def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """좌표 → 주소 문자열."""
    if not _map_credentials():
        logger.warning("NAVER Maps 키 미설정 — reverse_geocode skip")
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
            logger.warning(
                "reverse_geocode HTTP %s: %s", resp.status_code, resp.text[:200]
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
        logger.exception("reverse_geocode 실패: %s,%s", latitude, longitude)
        return None


def enrich_places_coordinates(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """좌표가 없는 장소에 geocode 를 시도해 보강."""
    enriched: list[dict[str, Any]] = []
    for p in places:
        item = dict(p)
        lat, lng = item.get("latitude"), item.get("longitude")
        if (lat is None or lng is None) and item.get("address"):
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
    FE 지도 렌더링용 payload.

    Returns:
        markers, polyline, available, current, render_hint
        render_hint: naver_js | st_map | text  (FE 가 Client ID 로 최종 결정)
    """
    markers: list[dict[str, Any]] = []
    polyline: list[list[float]] = []

    if (
        current_location
        and "latitude" in current_location
        and "longitude" in current_location
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
        markers.append(
            {
                "name": p.get("name", f"장소 {i}"),
                "lat": float(lat),
                "lng": float(lng),
                "order": i,
                "category": p.get("category"),
                "address": p.get("address"),
            }
        )
        polyline.append([float(lat), float(lng)])

    available = bool(markers)
    # FE: client_id 있으면 naver_js, 없으면 st_map, 좌표 없으면 text
    render_hint = "st_map" if available else "text"
    if available and _map_credentials():
        # geocode 키가 있으면 최소한 maps 연동 준비됨 — JS 는 client id 만으로도 가능
        render_hint = "naver_js"

    settings = get_settings()
    if available and (settings.naver_map_client_id or settings.naver_openapi_client_id):
        render_hint = "naver_js"
    elif available:
        render_hint = "st_map"

    return {
        "markers": markers,
        "polyline": polyline,
        "available": available,
        "current": current_location,
        "render_hint": render_hint,
        "marker_count": len(markers),
    }


def js_client_id() -> str | None:
    """Dynamic Map(JS) 용 Client ID (Secret 불필요)."""
    s = get_settings()
    return (s.naver_map_client_id or s.naver_openapi_client_id or "").strip() or None
