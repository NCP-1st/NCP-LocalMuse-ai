"""코스 결과 패널: 스토리 + 장소 카드 + 메타."""

from __future__ import annotations

from typing import Any

import streamlit as st

from FE.components.map_view import render_map
from FE.components.place_card import render_place_card


def render_course_result(
    result: dict[str, Any],
    *,
    naver_client_id: str | None = None,
) -> None:
    title = result.get("title") or "추천 코스"
    story = result.get("story") or ""
    places = result.get("places") or []
    source = result.get("source") or "-"
    course_id = result.get("course_id")
    candidates = result.get("candidates_count")
    message = result.get("message")

    if message and not places:
        st.error(message)
        return

    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.subheader(title)
    with head_r:
        badge = "ok" if source == "clova" else "warn"
        label = "AI (CLOVA)" if source == "clova" else "Fallback 임시 추천"
        st.markdown(
            f'<span class="lm-badge {badge}">{label}</span>',
            unsafe_allow_html=True,
        )
        if course_id is not None:
            st.caption(f"저장 ID: {course_id}")
        if candidates is not None:
            st.caption(f"후보 {candidates}곳")
        quality = result.get("quality") or {}
        if quality.get("score") is not None:
            st.caption(f"품질 {quality['score']}/100")

    if story:
        st.markdown("#### 지역 스토리")
        st.write(story)

    # 동선 한눈에
    if places:
        route_chips = " → ".join(
            f"**{i}. {p.get('name', '장소')}**" for i, p in enumerate(places, start=1)
        )
        st.markdown(f'<div class="lm-route">{route_chips}</div>', unsafe_allow_html=True)

    if not places:
        st.warning("추천 장소가 없습니다.")
        return

    st.divider()
    # 지도 (숫자 마커 · 화살표 동선 · 클릭 팝업 · 좌하단 루트 순서)
    render_map(
        result.get("route"),
        route_note=result.get("route_note"),
        naver_client_id=naver_client_id,
        places=places,
    )

    st.markdown("#### 추천 장소 상세")
    for i, place in enumerate(places, start=1):
        render_place_card(i, place)

    if message:
        st.info(message)
