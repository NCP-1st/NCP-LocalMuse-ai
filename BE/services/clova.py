"""
NAVER CLOVA Studio 연동 (Chat Completions) — Sprint A2.

역할 (PRD):
  - 여행 코스 생성
  - 추천 이유 생성
  - 지역 스토리 생성

파이프라인:
  1차 큐레이터 프롬프트 → JSON 추출
  → 후보 강제 바인딩·품질 보정
  → 실패 시 strict JSON 재시도 (Fallback Prompt)
  → 최종 deterministic fallback
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import requests

from BE.prompts.course import (
    SYSTEM_CURATOR,
    SYSTEM_JSON_STRICT,
    build_course_user_prompt,
    build_strict_retry_suffix,
)
from BE.services.course_quality import (
    default_travel_label,
    finalize_course,
    parse_time_budget_minutes,
    pick_diverse,
)
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
    실패·미설정 시 fallback 코스를 반환한다.
    """
    settings = get_settings()
    slim = [_slim_candidate(c) for c in candidates[:15]]

    if not settings.clova_api_key:
        if settings.allow_stub_without_keys:
            logger.warning("CLOVA_API_KEY 미설정 — fallback 코스 반환")
            return fallback_course(
                location=location,
                purpose=purpose,
                time=time,
                transport=transport,
                candidates=candidates,
                note="no_api_key",
            )
        raise ClovaError("CLOVA_API_KEY is not configured")

    # 일정 길이에 따라 장소 개수 힌트
    minutes = parse_time_budget_minutes(time)
    if minutes <= 90:
        count_hint = "3"
    elif minutes >= 300:
        count_hint = "4~5"
    else:
        count_hint = "3~5"

    user_prompt = build_course_user_prompt(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=slim,
        place_count_hint=count_hint,
    )

    # —— 1차 ——
    try:
        content = _chat_completions(system=SYSTEM_CURATOR, user=user_prompt)
        raw = extract_json_object(content)
        course = finalize_course(
            raw,
            candidates=candidates,
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
        )
        if len(course.get("places") or []) < 3:
            raise ClovaError("fewer than 3 places after finalize")
        course["source"] = "clova"
        course["attempt"] = 1
        return course
    except Exception as first_exc:
        logger.warning("CLOVA 1차 실패 — strict JSON 재시도: %s", first_exc)

    # —— 2차: Fallback Prompt (PRD) ——
    try:
        strict_user = (
            build_course_user_prompt(
                location=location,
                purpose=purpose,
                time=time,
                transport=transport,
                candidates=slim[:10],
                place_count_hint="3~5",
            )
            + build_strict_retry_suffix()
        )
        content = _chat_completions(
            system=SYSTEM_JSON_STRICT,
            user=strict_user,
            temperature=min(0.25, settings.clova_temperature),
        )
        raw = extract_json_object(content)
        course = finalize_course(
            raw,
            candidates=candidates,
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
        )
        if len(course.get("places") or []) < 3:
            raise ClovaError("fewer than 3 places after strict finalize")
        course["source"] = "clova"
        course["attempt"] = 2
        course["retry"] = "strict_json"
        return course
    except Exception as second_exc:
        logger.warning("CLOVA 2차 실패 → deterministic fallback: %s", second_exc)
        return fallback_course(
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
            candidates=candidates,
            note=f"clova_error:{type(second_exc).__name__}",
        )


def build_course_prompt(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
) -> str:
    """하위 호환 — 프롬프트 빌더 래퍼."""
    return build_course_user_prompt(
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
        candidates=candidates,
    )


def fallback_course(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    candidates: list[dict[str, Any]],
    note: str | None = None,
) -> dict[str, Any]:
    """CLOVA 실패/미설정 시 deterministic Fallback (PRD)."""
    selected = pick_diverse(candidates, limit=5)
    raw_places = []
    move = default_travel_label(transport)
    for i, c in enumerate(selected):
        raw_places.append(
            {
                "name": c.get("name", f"장소 {i + 1}"),
                "category": c.get("category", "-"),
                "address": c.get("address", ""),
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "duration": None,
                "travel_time": "출발" if i == 0 else move,
                "reason": (
                    f"{c.get('overview') or c.get('name')} — "
                    f"'{purpose}' 요청과 {location} 일정({time}, {transport})에 맞춰 선정했습니다."
                ),
                "content_id": c.get("content_id"),
                "image": c.get("image"),
            }
        )

    course = finalize_course(
        {
            "title": f"{location} {time} 로컬 코스",
            "story": (
                f"{location} 일대는 짧은 일정에도 카페·산책·문화 공간을 한 동선으로 "
                f"묶기 좋은 로컬 여행지입니다. ({transport} 이동 기준)"
            ),
            "places": raw_places,
            "route_note": "",
        },
        candidates=candidates or selected,
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
    )
    course["source"] = "fallback"
    if note:
        course["fallback_note"] = note
    return course


def _chat_completions(
    *,
    system: str,
    user: str,
    temperature: float | None = None,
) -> str:
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
    if settings.clova_apigw_api_key:
        headers["X-NCP-APIGW-API-KEY"] = settings.clova_apigw_api_key

    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": max(settings.clova_max_tokens, 1024),
        "temperature": (
            temperature if temperature is not None else min(settings.clova_temperature, 0.5)
        ),
        "repeatPenalty": 5.0,
        "stopBefore": [],
        "includeAiFilters": False,
    }

    resp = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=max(settings.http_timeout_sec, 45.0),
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


# —— 테스트 하위 호환 별칭 ——
def _normalize_course_json(
    data: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return finalize_course(
        data,
        candidates=candidates,
        location="서울",
        purpose="",
        time="3시간",
        transport="도보",
    )


def _ensure_place_count(
    course: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
    location: str,
    purpose: str,
    time: str,
    transport: str,
) -> dict[str, Any]:
    return finalize_course(
        course,
        candidates=candidates,
        location=location,
        purpose=purpose,
        time=time,
        transport=transport,
    )
