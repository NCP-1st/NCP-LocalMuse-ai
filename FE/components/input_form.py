"""여행 조건 입력 (사이드바). PRD: 위치 · 목적 · 시간 · 이동수단."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass
class TripFormData:
    location: str
    purpose: str
    time: str
    transport: str
    nickname: str
    submitted: bool


def render_sidebar_form(
    *,
    default_region: str = "서울",
    default_nickname: str = "guest",
) -> TripFormData:
    with st.sidebar:
        st.header("여행 조건")
        nickname = st.text_input("닉네임 (저장용)", value=default_nickname)
        location = st.text_input(
            "현재 위치 / 지역",
            value=default_region,
            help="위치 권한 거부 시 기본값: 서울 (PRD)",
            placeholder="예) 성수, 서울, 홍대",
        )
        purpose = st.text_area(
            "여행 목적 (자연어)",
            placeholder="예) 성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.",
            height=120,
        )
        time_budget = st.selectbox(
            "이용 가능 시간",
            options=["1시간", "2시간", "3시간", "4시간", "반나절", "하루"],
            index=2,
        )
        # 직접 입력도 허용
        time_custom = st.text_input("시간 직접 입력 (선택)", value="")
        transport = st.selectbox(
            "이동수단",
            options=["도보", "대중교통", "자동차", "자전거"],
            index=0,
        )
        submitted = st.button("코스 추천 받기", type="primary", use_container_width=True)

        st.divider()
        st.markdown("**Demo (PRD)**")
        st.caption(
            "성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘."
        )

    return TripFormData(
        location=(location or default_region).strip(),
        purpose=(purpose or "").strip(),
        time=(time_custom or time_budget).strip(),
        transport=transport,
        nickname=(nickname or "guest").strip(),
        submitted=submitted,
    )
