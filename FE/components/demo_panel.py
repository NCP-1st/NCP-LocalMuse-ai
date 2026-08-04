"""메인 화면 데모 원클릭 패널 — 선형 SVG 아이콘."""

from __future__ import annotations

import streamlit as st

from FE.components.icons import icon, icon_heading, icon_text
from FE.components.input_form import (
    DEMO_LOCATION,
    DEMO_PURPOSE,
    DEMO_TIME,
    DEMO_TRANSPORT,
    PRESETS,
    make_demo_on_click,
)


def render_demo_panel() -> None:
    st.markdown(
        icon_heading("zap", "데모 원클릭", level=3, size=20),
        unsafe_allow_html=True,
    )
    st.caption(
        "PRD Demo Scenario — 성수 3시간 감성 카페+산책. "
        "`.env` 키가 있으면 실데이터(TourAPI+CLOVA+Maps), 없으면 스텁으로 동일 플로우 실행."
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        st.info("시나리오")
        st.markdown(
            f"{icon_text('map-pin', DEMO_LOCATION)} · "
            f"{icon_text('clock', DEMO_TIME)} · "
            f"{icon_text('walk', DEMO_TRANSPORT)}",
            unsafe_allow_html=True,
        )
        st.markdown(icon_text("message", DEMO_PURPOSE), unsafe_allow_html=True)
    with c2:
        st.button(
            "지금 데모 실행",
            type="primary",
            use_container_width=True,
            key="btn_demo_main",
            on_click=make_demo_on_click(
                DEMO_LOCATION, DEMO_PURPOSE, DEMO_TIME, DEMO_TRANSPORT
            ),
        )

    st.markdown(
        f"{icon('list', size=16)} <b>빠른 프리셋</b>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(PRESETS))
    for col, (label, loc, purpose, t, tr) in zip(cols, PRESETS):
        with col:
            st.button(
                label,
                key=f"main_preset_{label}",
                use_container_width=True,
                on_click=make_demo_on_click(loc, purpose, t, tr),
            )
