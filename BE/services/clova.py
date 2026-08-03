"""
NAVER CLOVA Studio 연동 (Chat Completions).

역할 (PRD):
  - 여행 코스 생성
  - 추천 이유 생성
  - 지역 스토리 생성

컨벤션: Prompt 출력은 JSON 고정.
실패 시: Fallback Prompt / deterministic fallback (PRD Error Handling)
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import requests

from BE.utils.config import get_settings
from BE.utils.json_extract import extract_json_object

logger = logging.getLogger(__name__)


class ClovaError(RuntimeError):
    """CLOVA Studio 호출 실패."""


def generate_story(
    *,
    location: str,
    purpose: str,
    places: list[dict[str, Any]],
) -> str:
    """지역 스토리 / 코스 맥락 문단 생성."""
    result = complete_course_json(
        location=location,
        purpose=purpose,
        time="",
        transport="",
        candidates=places,
    )
    return str(result.get("story") or "")


def complete_course_json(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    CLOVA Studio에 코스 생성을 요청하고 JSON dict를 반환한다.
    실패·미설정 시 fallback 코스를 반환한다 (예외로 전체 실패시키지 않음).
    """
    settings = get_settings()
    slim_candidates = [_slim_candidate(c) for c in candidates[:15]]

    if not settings.clova_api_key:
        if settings.allow_stub_without_keys:
            logger.warning("CLOVA_API_KEY 미설정 — fallback 코스 반환")
            return fallback_course(
                location=location,
                purpose=purpose,
                time=time,
                transport=transport,
                candidates=candidates,
            )
        raise ClovaError("CLOVA_API_KEY is not configured")

    user_prompt = build_course_prompt(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=slim_candidates,
    )

    try:
        content = _chat_completions(
            system=(
                "당신은 한국 로컬 여행 큐레이터입니다. "
                "반드시 유효한 JSON 객체만 출력하세요. "
                "마크다운 코드블록·설명 문장 없이 JSON만 반환합니다."
            ),
            user=user_prompt,
        )
        data = extract_json_object(content)
        normalized = _normalize_course_json(data, candidates=candidates)
        if not normalized.get("places"):
            raise ClovaError("empty places in model JSON")
        normalized["source"] = "clova"
        return normalized
    except Exception as exc:
        logger.warning("CLOVA 실패 → fallback 사용: %s", exc)
        # PRD: Fallback Prompt / fallback result
        return fallback_course(
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
            candidates=candidates,
            note=f"clova_error:{type(exc).__name__}",
        )


def build_course_prompt(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
) -> str:
    """여행 큐레이터 프롬프트 (JSON 출력 고정)."""
    candidate_json = json.dumps(candidates, ensure_ascii=False, indent=2)
    return f"""사용자의 현재 위치와 관광 데이터를 참고하여 3~5개의 장소를 추천하세요.
후보 목록에 있는 장소 위주로 고르고, 동선이 자연스럽도록 방문 순서를 정하세요.
각 장소에 추천 이유(reason)를 구체적으로 적으세요.

[사용자 조건]
- 위치: {location}
- 목적: {purpose}
- 시간: {time}
- 이동수단: {transport}

[후보 장소 — TourAPI]
{candidate_json}

[출력 JSON 스키마 — 이 형식만 출력]
{{
  "title": "코스 제목",
  "story": "지역 스토리 1~3문장",
  "places": [
    {{
      "name": "장소명",
      "category": "카테고리",
      "address": "주소",
      "latitude": 0.0,
      "longitude": 0.0,
      "duration": "체류 시간",
      "travel_time": "이전 지점에서의 이동 시간",
      "reason": "추천 이유",
      "content_id": "후보 content_id"
    }}
  ],
  "route_note": "동선 한 줄 요약"
}}
"""


def fallback_course(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
    note: str | None = None,
) -> dict[str, Any]:
    """CLOVA 실패/미설정 시 Fallback (PRD)."""
    selected = _pick_diverse(candidates, limit=5)
    places: list[dict[str, Any]] = []
    for i, c in enumerate(selected):
        places.append(
            {
                "name": c.get("name", f"장소 {i + 1}"),
                "category": c.get("category", "-"),
                "address": c.get("address", ""),
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "duration": "40분",
                "travel_time": "도보 10분" if i else "출발",
                "reason": (
                    f"{c.get('overview') or c.get('name')} — "
                    f"'{purpose}' 요청과 {location} 일정({time}, {transport})에 맞춰 선정했습니다."
                ),
                "content_id": c.get("content_id"),
                "image": c.get("image"),
            }
        )

    result = {
        "title": f"{location} {time} 로컬 코스",
        "story": (
            f"{location} 일대는 짧은 일정에도 카페·산책·문화 공간을 한 동선으로 "
            f"묶기 좋은 로컬 여행지입니다. ({transport} 이동 기준)"
        ),
        "places": places,
        "route_note": " → ".join(p["name"] for p in places) if places else "",
        "source": "fallback",
    }
    if note:
        result["fallback_note"] = note
    return result


def _chat_completions(*, system: str, user: str) -> str:
    settings = get_settings()
    model = settings.clova_model
    url = f"{settings.clova_base_url}/v1/chat-completions/{model}"
    headers = {
        "Authorization": f"Bearer {settings.clova_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    request_id = settings.clova_request_id or str(uuid.uuid4())
    headers["X-NCP-CLOVASTUDIO-REQUEST-ID"] = request_id
    # legacy gateway key support
    if settings.clova_apigw_api_key:
        headers["X-NCP-APIGW-API-KEY"] = settings.clova_apigw_api_key

    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": settings.clova_max_tokens,
        "temperature": settings.clova_temperature,
        "repeatPenalty": 5.0,
        "stopBefore": [],
        "includeAiFilters": False,
    }

    resp = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=max(settings.http_timeout_sec, 30.0),
    )
    if resp.status_code >= 400:
        raise ClovaError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    payload = resp.json()
    status = (payload.get("status") or {}).get("code")
    if status and str(status) not in {"20000", "200", "0"}:
        msg = (payload.get("status") or {}).get("message", "")
        raise ClovaError(f"CLOVA status {status}: {msg}")

    result = payload.get("result") or {}
    message = result.get("message") or {}
    content = message.get("content")
    if not content:
        # OpenAI-compat style fallback
        choices = payload.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content")
    if not content:
        raise ClovaError(f"empty content: {payload!r}"[:400])
    return str(content)


def _slim_candidate(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "content_id": c.get("content_id"),
        "name": c.get("name"),
        "category": c.get("category"),
        "address": c.get("address"),
        "latitude": c.get("latitude"),
        "longitude": c.get("longitude"),
        "overview": (c.get("overview") or "")[:180],
    }


def _normalize_course_json(
    data: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {
        str(c.get("content_id")): c
        for c in candidates
        if c.get("content_id") is not None
    }
    by_name = {str(c.get("name", "")).strip(): c for c in candidates}

    places_in = data.get("places") or data.get("course") or []
    places: list[dict[str, Any]] = []
    if isinstance(places_in, dict):
        places_in = [places_in]

    for p in places_in:
        if not isinstance(p, dict):
            continue
        cid = str(p.get("content_id") or "") or None
        name = str(p.get("name") or "").strip()
        base = (by_id.get(cid) if cid else None) or by_name.get(name) or {}
        places.append(
            {
                "name": name or base.get("name") or "장소",
                "category": p.get("category") or base.get("category") or "-",
                "address": p.get("address") or base.get("address") or "",
                "latitude": _num(p.get("latitude"), base.get("latitude")),
                "longitude": _num(p.get("longitude"), base.get("longitude")),
                "duration": p.get("duration") or "40분",
                "travel_time": p.get("travel_time") or "",
                "reason": p.get("reason") or p.get("why") or "",
                "content_id": cid or base.get("content_id"),
                "image": p.get("image") or base.get("image"),
            }
        )

    # 3~5개로 클램프
    places = places[:5]
    return {
        "title": data.get("title") or "추천 로컬 코스",
        "story": data.get("story") or data.get("region_story") or "",
        "places": places,
        "route_note": data.get("route_note")
        or " → ".join(x["name"] for x in places),
    }


def _num(primary: Any, secondary: Any = None) -> float | None:
    for v in (primary, secondary):
        if v is None or v == "":
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _pick_diverse(candidates: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """카테고리 다양성을 우선해 후보를 고른다."""
    if not candidates:
        return []
    picked: list[dict[str, Any]] = []
    used_cat: set[str] = set()
    # 1차: 카테고리 안 겹치게
    for c in candidates:
        cat = str(c.get("category") or "")
        if cat in used_cat:
            continue
        picked.append(c)
        used_cat.add(cat)
        if len(picked) >= limit:
            return picked
    # 2차: 나머지 채우기
    for c in candidates:
        if c in picked:
            continue
        picked.append(c)
        if len(picked) >= limit:
            break
    return picked
