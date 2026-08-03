"""
한국관광공사 TourAPI (KorService1) 연동.

PRD 카테고리:
  - 관광지 (contentTypeId=12)
  - 문화시설 (14)
  - 음식점 (39)
  - Overview (detailCommon1)

실패 시: 재시도 → 스텁/빈 결과 (course 레이어에서 메시지 처리)
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import unquote

import requests

from BE.utils.config import get_settings
from BE.utils.regions import content_type_name, extract_search_keyword, resolve_area_code
from BE.utils.retry import with_retry

logger = logging.getLogger(__name__)

# PRD 주요 타입
CONTENT_TYPES_MVP = ("12", "14", "39")  # 관광지, 문화시설, 음식점


class TourAPIError(RuntimeError):
    """TourAPI 호출 실패."""


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
        name, address, latitude, longitude, category, overview,
        content_id, content_type_id, image
    """
    settings = get_settings()
    region = (region or settings.default_region).strip()
    area_code = resolve_area_code(region)
    search_kw = extract_search_keyword(region, keyword)

    if not settings.tour_api_key:
        if settings.allow_stub_without_keys:
            logger.warning("TOUR_API_KEY 미설정 — 스텁 후보 사용")
            return _stub_locations(region, keyword)
        raise TourAPIError("TOUR_API_KEY is not configured")

    types = (content_type,) if content_type else CONTENT_TYPES_MVP
    collected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for ct in types:
        try:
            rows = with_retry(
                lambda ct=ct: _search_keyword(
                    keyword=search_kw,
                    area_code=area_code,
                    content_type_id=ct,
                    num_of_rows=max(5, max_items // max(1, len(types))),
                ),
                retries=settings.tour_api_retries,
                label=f"TourAPI searchKeyword ct={ct}",
            )
        except Exception:
            logger.exception("TourAPI contentType=%s 조회 실패", ct)
            continue

        for row in rows:
            cid = str(row.get("content_id") or row.get("name"))
            if cid in seen:
                continue
            seen.add(cid)
            collected.append(row)
            if len(collected) >= max_items:
                return collected[:max_items]

    # keyword 가 약하면 지역 기반 목록으로 보강
    if len(collected) < min(5, max_items) and area_code is not None:
        for ct in types:
            try:
                rows = with_retry(
                    lambda ct=ct: _area_based_list(
                        area_code=area_code,
                        content_type_id=ct,
                        num_of_rows=10,
                    ),
                    retries=settings.tour_api_retries,
                    label=f"TourAPI areaBasedList ct={ct}",
                )
            except Exception:
                logger.exception("TourAPI areaBasedList ct=%s 실패", ct)
                continue
            for row in rows:
                cid = str(row.get("content_id") or row.get("name"))
                if cid in seen:
                    continue
                seen.add(cid)
                collected.append(row)
                if len(collected) >= max_items:
                    break
            if len(collected) >= max_items:
                break

    if not collected and settings.allow_stub_without_keys:
        logger.warning("TourAPI 결과 없음 — 스텁 후보로 폴백")
        return _stub_locations(region, keyword)

    return collected[:max_items]


def get_overview(content_id: str, content_type_id: str | int | None = None) -> str:
    """detailCommon1 로 overview 조회. 실패 시 빈 문자열."""
    settings = get_settings()
    if not settings.tour_api_key or not content_id:
        return ""

    def _call() -> str:
        params = _base_params(settings)
        params.update(
            {
                "contentId": content_id,
                "defaultYN": "Y",
                "overviewYN": "Y",
            }
        )
        if content_type_id:
            params["contentTypeId"] = str(content_type_id)
        url = f"{settings.tour_api_base_url}/detailCommon1"
        resp = requests.get(url, params=params, timeout=settings.http_timeout_sec)
        resp.raise_for_status()
        items = _extract_items(resp.json())
        if not items:
            return ""
        return str(items[0].get("overview") or "").strip()

    try:
        return with_retry(_call, retries=1, label="TourAPI detailCommon")
    except Exception:
        logger.exception("overview 조회 실패 contentId=%s", content_id)
        return ""


def _base_params(settings: Any) -> dict[str, Any]:
    # data.go.kr 키에 % 가 이중 인코딩된 경우가 있어 unquote
    key = unquote(settings.tour_api_key)
    return {
        "serviceKey": key,
        "MobileOS": "ETC",
        "MobileApp": settings.tour_api_mobile_app,
        "_type": "json",
    }


def _search_keyword(
    *,
    keyword: str,
    area_code: int | None,
    content_type_id: str,
    num_of_rows: int = 10,
) -> list[dict[str, Any]]:
    settings = get_settings()
    params = _base_params(settings)
    params.update(
        {
            "keyword": keyword,
            "contentTypeId": content_type_id,
            "arrange": "C",  # 수정일 순
            "numOfRows": num_of_rows,
            "pageNo": 1,
            "listYN": "Y",
        }
    )
    if area_code is not None:
        params["areaCode"] = area_code

    url = f"{settings.tour_api_base_url}/searchKeyword1"
    resp = requests.get(url, params=params, timeout=settings.http_timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    _raise_if_tour_error(data)
    return [_normalize_item(it) for it in _extract_items(data)]


def _area_based_list(
    *,
    area_code: int,
    content_type_id: str,
    num_of_rows: int = 10,
) -> list[dict[str, Any]]:
    settings = get_settings()
    params = _base_params(settings)
    params.update(
        {
            "areaCode": area_code,
            "contentTypeId": content_type_id,
            "arrange": "C",
            "numOfRows": num_of_rows,
            "pageNo": 1,
            "listYN": "Y",
        }
    )
    url = f"{settings.tour_api_base_url}/areaBasedList1"
    resp = requests.get(url, params=params, timeout=settings.http_timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    _raise_if_tour_error(data)
    return [_normalize_item(it) for it in _extract_items(data)]


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        body = payload["response"]["body"]
        items = body.get("items")
        if not items:
            return []
        item = items.get("item")
        if item is None:
            return []
        if isinstance(item, list):
            return item
        if isinstance(item, dict):
            return [item]
        return []
    except (KeyError, TypeError):
        return []


def _raise_if_tour_error(payload: dict[str, Any]) -> None:
    try:
        header = payload["response"]["header"]
    except (KeyError, TypeError) as exc:
        raise TourAPIError(f"unexpected TourAPI payload: {payload!r}") from exc
    code = str(header.get("resultCode", ""))
    if code not in {"0000", "0"}:
        msg = header.get("resultMsg", "unknown error")
        raise TourAPIError(f"TourAPI error {code}: {msg}")


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    lat = _to_float(item.get("mapy") or item.get("mapY"))
    lng = _to_float(item.get("mapx") or item.get("mapX"))
    ct = item.get("contenttypeid") or item.get("contentTypeId")
    return {
        "content_id": str(item.get("contentid") or item.get("contentId") or ""),
        "content_type_id": str(ct) if ct is not None else None,
        "name": str(item.get("title") or "").strip(),
        "address": str(
            item.get("addr1") or item.get("addr") or item.get("address") or ""
        ).strip(),
        "latitude": lat,
        "longitude": lng,
        "category": content_type_name(ct),
        "overview": str(item.get("overview") or "").strip(),
        "image": str(item.get("firstimage") or item.get("firstimage2") or "").strip()
        or None,
        "tel": str(item.get("tel") or "").strip() or None,
    }


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stub_locations(region: str, keyword: str | None) -> list[dict[str, Any]]:
    """API 키 없거나 결과 없을 때 개발용 더미 후보."""
    base = region or "서울"
    hint = keyword or "로컬"
    return [
        {
            "content_id": "stub-1",
            "content_type_id": "39",
            "name": f"{base} 감성 카페 A",
            "address": f"{base} 예시로 1길 1",
            "latitude": 37.5445,
            "longitude": 127.0557,
            "category": "음식점",
            "overview": f"{hint} 분위기 카페 (TourAPI 스텁)",
            "image": None,
            "tel": None,
        },
        {
            "content_id": "stub-2",
            "content_type_id": "12",
            "name": f"{base} 산책 명소 B",
            "address": f"{base} 예시로 2길 2",
            "latitude": 37.5470,
            "longitude": 127.0600,
            "category": "관광지",
            "overview": "가벼운 산책 코스 (TourAPI 스텁)",
            "image": None,
            "tel": None,
        },
        {
            "content_id": "stub-3",
            "content_type_id": "14",
            "name": f"{base} 문화공간 C",
            "address": f"{base} 예시로 3길 3",
            "latitude": 37.5410,
            "longitude": 127.0520,
            "category": "문화시설",
            "overview": "전시·문화 (TourAPI 스텁)",
            "image": None,
            "tel": None,
        },
        {
            "content_id": "stub-4",
            "content_type_id": "39",
            "name": f"{base} 로컬 식당 D",
            "address": f"{base} 예시로 4길 4",
            "latitude": 37.5430,
            "longitude": 127.0580,
            "category": "음식점",
            "overview": "식사 (TourAPI 스텁)",
            "image": None,
            "tel": None,
        },
        {
            "content_id": "stub-5",
            "content_type_id": "12",
            "name": f"{base} 골목 스팟 E",
            "address": f"{base} 예시로 5길 5",
            "latitude": 37.5455,
            "longitude": 127.0565,
            "category": "관광지",
            "overview": "로컬 분위기 골목 (TourAPI 스텁)",
            "image": None,
            "tel": None,
        },
    ]
