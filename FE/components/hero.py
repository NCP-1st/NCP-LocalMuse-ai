"""상단 히어로 / 소개."""

from __future__ import annotations

import streamlit as st


def render_hero() -> None:
    st.markdown(
        """
<div class="lm-hero">
  <h1>🧭 LocalMuse AI</h1>
  <p class="lm-muted">
    AI가 취향과 현재 상황을 분석해 <b>오늘 가장 적합한 로컬 여행 코스</b>를 추천합니다.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("PC Web · Streamlit · CLOVA Studio · TourAPI · NAVER Maps · NCP")
