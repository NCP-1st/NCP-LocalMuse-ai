"""LLM 응답 텍스트에서 JSON 객체를 안전하게 추출."""

from __future__ import annotations

import json
import re
from typing import Any


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def extract_json_object(text: str) -> dict[str, Any]:
    """
    모델 출력에서 첫 번째 JSON object 를 파싱한다.
    code fence 또는 앞뒤 설명 문구가 있어도 최대한 복구한다.
    """
    if not text or not text.strip():
        raise ValueError("empty model response")

    raw = text.strip()

    fence = _FENCE_RE.search(raw)
    if fence:
        raw = fence.group(1).strip()

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        snippet = raw[start : end + 1]
        data = json.loads(snippet)
        if isinstance(data, dict):
            return data

    raise ValueError("JSON object not found in model response")
