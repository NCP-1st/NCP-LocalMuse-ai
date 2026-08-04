"""코스 JSON 품질 검증·보정 (A2)."""

from __future__ import annotations

import re
from typing import Any

_MIN_PLACES = 3
_MAX_PLACES = 5


def parse_time_budget_minutes(time_str: str) -> int:
    """이용 가능 시간을 분 단위로 추정."""
    t = (time_str or "").strip()
    if "반나절" in t:
        return 240
    if "하루" in t or "종일" in t:
        return 480
    m = re.search(r"(\d+)\s*시간", t)
    if m:
        return int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*분", t)
    if m:
        return int(m.group(1))
    return 180


def default_travel_label(transport: str) -> str:
    t = (transport or "").strip()
    if "자동차" in t or t == "차":
        return "차량 10분"
    if "대중" in t or "지하철" in t or "버스" in t:
        return "대중교통 15분"
    if "자전거" in t:
        return "자전거 12분"
    return "도보 10분"


def pick_diverse(candidates: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    if not candidates:
        return []
    picked: list[dict[str, Any]] = []
    used_cat: set[str] = set()
    for c in candidates:
        cat = str(c.get("category") or "")
        if cat in used_cat:
            continue
        picked.append(c)
        used_cat.add(cat)
        if len(picked) >= limit:
            return picked
    for c in candidates:
        if c in picked:
            continue
        picked.append(c)
        if len(picked) >= limit:
            break
    return picked


def bind_to_candidates(
    places: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    모델이 만든 장소를 후보에 강제 바인딩.
    후보에 매칭되지 않으면 해당 항목 제거 (할루시네이션 차단).
    """
    by_id = {
        str(c.get("content_id")): c
        for c in candidates
        if c.get("content_id") is not None
    }
    by_name = {str(c.get("name") or "").strip(): c for c in candidates}

    bound: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    for p in places:
        if not isinstance(p, dict):
            continue
        cid = str(p.get("content_id") or "").strip() or None
        name = str(p.get("name") or "").strip()
        base = (by_id.get(cid) if cid else None) or by_name.get(name)

        if not base and name:
            for k, v in by_name.items():
                if not k:
                    continue
                if name in k or k in name:
                    base = v
                    break

        if not base:
            # 후보 밖 장소는 버림
            continue

        key = str(base.get("content_id") or base.get("name"))
        if key in used_keys:
            continue
        used_keys.add(key)

        bound.append(
            {
                "name": base.get("name") or name or "장소",
                "category": p.get("category") or base.get("category") or "-",
                "address": base.get("address") or p.get("address") or "",
                "latitude": _num(base.get("latitude"), p.get("latitude")),
                "longitude": _num(base.get("longitude"), p.get("longitude")),
                "duration": str(p.get("duration") or "").strip() or None,
                "travel_time": str(p.get("travel_time") or "").strip() or None,
                "reason": str(p.get("reason") or p.get("why") or "").strip(),
                "content_id": base.get("content_id"),
                "image": base.get("image") or p.get("image"),
            }
        )
        if len(bound) >= _MAX_PLACES:
            break

    return bound


def fill_durations(
    places: list[dict[str, Any]],
    *,
    time_budget: str,
    transport: str,
) -> list[dict[str, Any]]:
    """체류/이동 시간 비어 있으면 일정에 맞게 배분."""
    total = parse_time_budget_minutes(time_budget)
    n = max(len(places), 1)
    # 이동 여유 약 20%
    stay_pool = max(int(total * 0.8), n * 25)
    per = max(stay_pool // n, 25)
    move = default_travel_label(transport)

    out: list[dict[str, Any]] = []
    for i, p in enumerate(places):
        item = dict(p)
        if not item.get("duration"):
            item["duration"] = f"{per}분"
        if not item.get("travel_time"):
            item["travel_time"] = "출발" if i == 0 else move
        if not item.get("reason"):
            item["reason"] = f"{item.get('name')} — 일정과 목적에 맞춰 추천합니다."
        out.append(item)
    return out


def ensure_min_places(
    places: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    *,
    purpose: str,
    transport: str,
) -> list[dict[str, Any]]:
    if len(places) >= _MIN_PLACES:
        return places[:_MAX_PLACES]

    used = {str(p.get("content_id") or p.get("name")) for p in places}
    move = default_travel_label(transport)
    result = list(places)

    for c in pick_diverse(candidates, limit=8):
        key = str(c.get("content_id") or c.get("name"))
        if key in used:
            continue
        result.append(
            {
                "name": c.get("name"),
                "category": c.get("category", "-"),
                "address": c.get("address", ""),
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "duration": None,
                "travel_time": move if result else "출발",
                "reason": f"{purpose} 일정에 맞춰 후보에서 보완 선정했습니다.",
                "content_id": c.get("content_id"),
                "image": c.get("image"),
            }
        )
        used.add(key)
        if len(result) >= _MIN_PLACES:
            break
    return result[:_MAX_PLACES]


def finalize_course(
    raw: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
    location: str,
    purpose: str,
    time: str,
    transport: str,
) -> dict[str, Any]:
    """normalize + bind + pad + fill → 품질 메타 포함 최종 코스."""
    places_in = raw.get("places") or raw.get("course") or []
    if isinstance(places_in, dict):
        places_in = [places_in]
    if not isinstance(places_in, list):
        places_in = []

    bound = bind_to_candidates(places_in, candidates)
    padded = ensure_min_places(
        bound, candidates, purpose=purpose, transport=transport
    )
    filled = fill_durations(padded, time_budget=time, transport=transport)

    title = str(raw.get("title") or "").strip() or f"{location} {time} 로컬 코스"
    story = str(raw.get("story") or raw.get("region_story") or "").strip()
    if not story:
        story = (
            f"{location} 일대는 짧은 일정에도 카페·산책·문화 공간을 "
            f"한 동선으로 묶기 좋은 로컬 여행지입니다. ({transport} 이동 기준)"
        )

    route_note = str(raw.get("route_note") or "").strip()
    if not route_note:
        route_note = " → ".join(
            str(p.get("name")) for p in filled if p.get("name")
        )

    quality = score_quality(filled, story=story, title=title)

    return {
        "title": title,
        "story": story,
        "places": filled,
        "route_note": route_note,
        "quality": quality,
    }


def score_quality(
    places: list[dict[str, Any]],
    *,
    story: str,
    title: str,
) -> dict[str, Any]:
    """간단한 품질 점수 (0~100)."""
    issues: list[str] = []
    score = 100

    n = len(places)
    if n < _MIN_PLACES:
        score -= 40
        issues.append(f"places<{_MIN_PLACES}")
    elif n > _MAX_PLACES:
        score -= 10
        issues.append(f"places>{_MAX_PLACES}")

    if not story or len(story) < 10:
        score -= 15
        issues.append("weak_story")
    if not title:
        score -= 10
        issues.append("empty_title")

    with_reason = sum(1 for p in places if (p.get("reason") or "").strip())
    if places and with_reason < len(places):
        score -= 5 * (len(places) - with_reason)
        issues.append("missing_reason")

    with_coords = sum(
        1
        for p in places
        if p.get("latitude") is not None and p.get("longitude") is not None
    )
    if places and with_coords < len(places):
        score -= 5 * (len(places) - with_coords)
        issues.append("missing_coords")

    cats = {str(p.get("category") or "") for p in places}
    if len(cats) == 1 and n >= 3:
        score -= 5
        issues.append("low_category_diversity")

    score = max(0, min(100, score))
    return {
        "score": score,
        "place_count": n,
        "with_reason": with_reason,
        "with_coords": with_coords,
        "categories": sorted(c for c in cats if c),
        "issues": issues,
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
