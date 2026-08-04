"""상단 히어로 / 소개."""

from __future__ import annotations

import streamlit as st

from FE.components.icons import icon_heading


def render_hero() -> None:
    st.markdown(
        icon_heading("compass", "LocalMuse AI", level=1, size=28),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="lm-muted">'
        "AI가 취향과 현재 상황을 분석해 <b>오늘 가장 적합한 로컬 여행 코스</b>를 추천합니다."
        "</p>",
        unsafe_allow_html=True,
    )
    st.caption("PC Web · Streamlit · CLOVA Studio · TourAPI · NAVER Maps · NCP")
