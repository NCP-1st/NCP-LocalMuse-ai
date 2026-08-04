"""LLM 응답 텍스트에서 JSON 객체를 안전하게 추출·복구."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def extract_json_object(text: str) -> dict[str, Any]:
    """
    모델 출력에서 첫 번째 JSON object 를 파싱한다.
    code fence, 앞뒤 설명, trailing comma 등을 최대한 복구한다.
    """
    if not text or not text.strip():
        raise ValueError("empty model response")

    raw = text.strip()

    fence = _FENCE_RE.search(raw)
    if fence:
        raw = fence.group(1).strip()

    for candidate in _candidate_snippets(raw):
        parsed = _try_load_dict(candidate)
        if parsed is not None:
            return parsed

    raise ValueError("JSON object not found in model response")


def _candidate_snippets(raw: str) -> list[str]:
    out: list[str] = [raw]
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        out.append(raw[start : end + 1])
    return out


def _try_load_dict(snippet: str) -> dict[str, Any] | None:
    attempts = [
        snippet,
        _TRAILING_COMMA_RE.sub(r"\1", snippet),
        _TRAILING_COMMA_RE.sub(r"\1", snippet).replace("\u201c", '"').replace("\u201d", '"'),
    ]
    # 단일 따옴표 JSON 유사 케이스 (단순 치환 — 마지막 수단)
    if "'" in snippet and '"' not in snippet:
        attempts.append(snippet.replace("'", '"'))

    for attempt in attempts:
        try:
            data = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # 모델이 places 배열만 준 경우
            return {"places": data, "title": "", "story": "", "route_note": ""}
    return None
