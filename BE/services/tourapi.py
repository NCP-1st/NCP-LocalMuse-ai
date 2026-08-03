"""
한국관광공사 TourAPI 연동.

사용 카테고리 (PRD):
  - 관광지 (Tourist Spot)
  - 음식점 (Restaurant)
  - 문화시설 (Culture)
  - 여행지 Overview

실패 시: 재시도 → 안내 메시지 (PRD Error Handling)
"""

from __future__ import annotations

import logging
from typing import Any

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)


def get_location(
    region: str,
    *,
    keyword: str | None = None,
    content_type: str | None = None,
    max_items: int = 20,
) -> list[dict[str, Any]]:
    """
    TourAPI에서 장소 후보를 조회한다.

    Returns:
        Location-like dict list:
        name, address, latitude, longitude, category, overview
    """
    settings = get_settings()
    if not settings.tour_api_key:
        logger.warning("TOUR_API_KEY 미설정 — 빈 후보 리스트 반환 (스텁)")
        return _stub_locations(region, keyword)

    # TODO: TourAPI 실연동 (areaBasedList / searchKeyword / detailCommon 등)
    logger.info(
        "TourAPI 조회 예정: region=%s keyword=%s type=%s",
        region,
        keyword,
        content_type,
    )
    return _stub_locations(region, keyword)


def _stub_locations(region: str, keyword: str | None) -> list[dict[str, Any]]:
    """API 키 없거나 미구현 시 개발용 더미 후보."""
    base = region or "서울"
    hint = keyword or "로컬"
    return [
        {
            "name": f"{base} 감성 카페 A",
            "address": f"{base} 예시로 1길 1",
            "latitude": 37.5445,
            "longitude": 127.0557,
            "category": "카페",
            "overview": f"{hint} 분위기 카페 (TourAPI 스텁)",
        },
        {
            "name": f"{base} 산책 명소 B",
            "address": f"{base} 예시로 2길 2",
            "latitude": 37.5470,
            "longitude": 127.0600,
            "category": "산책",
            "overview": "가벼운 산책 코스 (TourAPI 스텁)",
        },
        {
            "name": f"{base} 문화공간 C",
            "address": f"{base} 예시로 3길 3",
            "latitude": 37.5410,
            "longitude": 127.0520,
            "category": "문화시설",
            "overview": "전시·문화 (TourAPI 스텁)",
        },
        {
            "name": f"{base} 로컬 식당 D",
            "address": f"{base} 예시로 4길 4",
            "latitude": 37.5430,
            "longitude": 127.0580,
            "category": "음식점",
            "overview": "식사 (TourAPI 스텁)",
        },
    ]
