"""실데이터 vs 스텁 배지 (선형 SVG)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from FE.components.icons import icon


def render_live_badge(result: dict[str, Any], *, maps_js: bool) -> None:
    integ = result.get("integration") or {}
    places = result.get("places") or []
    stub_n = sum(
        1 for p in places if str(p.get("content_id") or "").startswith("stub")
    )
    route = result.get("route") or {}
    markers = len(route.get("markers") or [])

    tour_live = bool(integ.get("tour_live"))
    if not integ:
        tour_live = len(places) > 0 and stub_n == 0
    clova_live = bool(integ.get("clova_live")) or result.get("source") == "clova"
    map_js = bool(integ.get("maps_js")) if integ else maps_js
    map_render = integ.get("map_render") or route.get("render_hint") or "text"
    map_live = bool(route.get("available")) and map_js and map_render == "naver_js"
    saved = bool(result.get("saved") or result.get("course_id"))
    db_kind = result.get("db_kind") or integ.get("db_kind") or integ.get("db") or "-"

    bits = [
        _bit("TourAPI", tour_live, "live" if tour_live else f"stub {stub_n}"),
        _bit("CLOVA", clova_live, result.get("source") or "-"),
        _bit(
            "Maps",
            bool(route.get("available")),
            f"{map_render} · {markers} markers",
        ),
        _bit("저장", saved, f"{db_kind}" + (f" #{result.get('course_id')}" if result.get("course_id") else "")),
    ]

    st.markdown(
        '<div class="lm-icon-row" style="flex-wrap:wrap;gap:0.75rem;margin:0.5rem 0 1rem 0">'
        + "".join(bits)
        + "</div>",
        unsafe_allow_html=True,
    )

    if tour_live and clova_live and map_live:
        st.success("실데이터 연동 — TourAPI + CLOVA + NAVER Maps")
    elif tour_live and clova_live:
        st.info(
            "TourAPI·CLOVA 실연동. "
            + (
                "지도는 좌표 기반 표시 중 (Dynamic Map Client ID 확인)."
                if route.get("available")
                else "지도 좌표가 부족합니다."
            )
        )
    else:
        st.caption(
            "일부 스텁/폴백일 수 있습니다. `.env` 키와 시스템 상태 페이지를 확인하세요."
        )


def _bit(label: str, ok: bool, detail: str) -> str:
    ic = (
        icon("check-circle", size=14, class_name="lm-icon lm-icon-ok")
        if ok
        else icon("circle", size=14, class_name="lm-icon lm-icon-muted")
    )
    return (
        f'<span class="lm-badge" style="display:inline-flex;align-items:center;gap:0.3rem">'
        f"{ic} {label}: {detail}</span>"
    )
