"""여행 조건 입력 (사이드바). PRD: 위치 · 목적 · 시간 · 이동수단 + 데모 원클릭."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

# PRD Demo Scenario
DEMO_LOCATION = "성수"
DEMO_PURPOSE = "성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘."
DEMO_TIME = "3시간"
DEMO_TRANSPORT = "도보"

PRESETS = [
    ("성수 감성 카페", "성수", DEMO_PURPOSE, "3시간", "도보"),
    ("홍대 데이트", "홍대", "홍대에서 반나절 데이트 코스 추천해줘. 카페와 산책 위주로.", "반나절", "도보"),
    ("을지로 맛집", "을지로", "을지로에서 2시간 맛집과 골목 산책 코스 추천해줘.", "2시간", "도보"),
]


@dataclass
class TripFormData:
    location: str
    purpose: str
    time: str
    transport: str
    nickname: str
    submitted: bool
    is_demo: bool = False


def render_sidebar_form(
    *,
    default_region: str = "서울",
    default_nickname: str = "guest",
) -> TripFormData:
    # 위젯 기본값: session_state 우선 (데모 원클릭용)
    if "form_location" not in st.session_state:
        st.session_state["form_location"] = default_region
    if "form_purpose" not in st.session_state:
        st.session_state["form_purpose"] = ""
    if "form_time" not in st.session_state:
        st.session_state["form_time"] = "3시간"
    if "form_transport" not in st.session_state:
        st.session_state["form_transport"] = "도보"
    if "form_nickname" not in st.session_state:
        st.session_state["form_nickname"] = default_nickname

    is_demo = bool(st.session_state.pop("demo_submit", False))

    with st.sidebar:
        st.header("여행 조건")
        st.text_input("닉네임 (저장용)", key="form_nickname")
        st.text_input(
            "현재 위치 / 지역",
            key="form_location",
            help="위치 권한 거부 시 기본값: 서울 (PRD)",
            placeholder="예) 성수, 서울, 홍대",
        )
        st.text_area(
            "여행 목적 (자연어)",
            key="form_purpose",
            placeholder=DEMO_PURPOSE,
            height=120,
        )
        st.selectbox(
            "이용 가능 시간",
            options=["1시간", "2시간", "3시간", "4시간", "반나절", "하루"],
            key="form_time",
        )
        st.selectbox(
            "이동수단",
            options=["도보", "대중교통", "자동차", "자전거"],
            key="form_transport",
        )
        submitted = st.button(
            "코스 추천 받기",
            type="primary",
            use_container_width=True,
            key="btn_submit_course",
        )

        st.divider()
        st.markdown("**⚡ 데모 원클릭 (PRD)**")
        if st.button(
            "성수 3시간 · 감성 카페+산책",
            use_container_width=True,
            type="secondary",
            key="btn_demo_prd",
        ):
            _apply_demo(DEMO_LOCATION, DEMO_PURPOSE, DEMO_TIME, DEMO_TRANSPORT)
            st.rerun()

        with st.expander("다른 프리셋", expanded=False):
            for label, loc, purpose, t, tr in PRESETS[1:]:
                if st.button(label, key=f"preset_{label}", use_container_width=True):
                    _apply_demo(loc, purpose, t, tr)
                    st.rerun()

        st.caption("데모 클릭 시 입력란을 채우고 바로 추천을 실행합니다.")

    # 데모 직후 자동 submit
    if is_demo:
        submitted = True

    return TripFormData(
        location=(st.session_state.get("form_location") or default_region).strip(),
        purpose=(st.session_state.get("form_purpose") or "").strip(),
        time=(st.session_state.get("form_time") or "3시간").strip(),
        transport=(st.session_state.get("form_transport") or "도보").strip(),
        nickname=(st.session_state.get("form_nickname") or "guest").strip(),
        submitted=submitted,
        is_demo=is_demo,
    )


def _apply_demo(location: str, purpose: str, time: str, transport: str) -> None:
    st.session_state["form_location"] = location
    st.session_state["form_purpose"] = purpose
    st.session_state["form_time"] = time
    st.session_state["form_transport"] = transport
    st.session_state["demo_submit"] = True
