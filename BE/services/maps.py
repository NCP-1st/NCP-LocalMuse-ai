"""
NAVER Maps API 연동.

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

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)


def geocode(address: str) -> dict[str, float] | None:
    """주소 → {latitude, longitude}."""
    settings = get_settings()
    if not settings.naver_map_client_id:
        logger.warning("NAVER Maps 키 미설정 — geocode 스텁 None")
        return None
    # TODO: NAVER Geocoding API
    return None


def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """좌표 → 주소 문자열."""
    settings = get_settings()
    if not settings.naver_map_client_id:
        logger.warning("NAVER Maps 키 미설정 — reverse_geocode 스텁 None")
        return None
    # TODO: NAVER Reverse Geocoding API
    return None


def build_route_payload(places: list[dict[str, Any]]) -> dict[str, Any]:
    """
    FE 지도 렌더링용 payload.

    Returns:
        markers: [{name, lat, lng, order}, ...]
        polyline: [[lat, lng], ...]
    """
    markers = []
    polyline: list[list[float]] = []
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
            }
        )
        polyline.append([float(lat), float(lng)])

    return {
        "markers": markers,
        "polyline": polyline,
        "available": bool(markers),
    }
