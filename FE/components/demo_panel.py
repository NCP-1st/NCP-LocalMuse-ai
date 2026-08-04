"""메인 화면 데모 원클릭 패널 (Sprint A4 / PRD Demo Scenario)."""

from __future__ import annotations

import streamlit as st

from FE.components.input_form import (
    DEMO_LOCATION,
    DEMO_PURPOSE,
    DEMO_TIME,
    DEMO_TRANSPORT,
    PRESETS,
    _apply_demo,
)


def render_demo_panel() -> None:
    st.markdown("### ⚡ 데모 원클릭")
    st.caption("PRD Demo Scenario — 입력 없이 바로 코스 생성 플로우를 실행합니다.")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.info(
            f"**시나리오**  \n"
            f"📍 {DEMO_LOCATION} · ⏱ {DEMO_TIME} · 🚶 {DEMO_TRANSPORT}  \n"
            f"💬 {DEMO_PURPOSE}"
        )
    with c2:
        if st.button(
            "지금 데모 실행",
            type="primary",
            use_container_width=True,
            key="btn_demo_main",
        ):
            _apply_demo(DEMO_LOCATION, DEMO_PURPOSE, DEMO_TIME, DEMO_TRANSPORT)
            st.rerun()

    st.markdown("**빠른 프리셋**")
    cols = st.columns(len(PRESETS))
    for col, (label, loc, purpose, t, tr) in zip(cols, PRESETS):
        with col:
            if st.button(label, key=f"main_preset_{label}", use_container_width=True):
                _apply_demo(loc, purpose, t, tr)
                st.rerun()
