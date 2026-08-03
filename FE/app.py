"""
LocalMuse AI — Streamlit Frontend entrypoint.

PRD User Flow:
  Start → 현재 위치 허용 → 여행 목적 입력 → AI 요청
       → 코스 생성 → 지도 출력 → 장소 상세 확인 → 종료
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 레포 루트를 path에 넣어 BE 패키지를 import 가능하게 함
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from BE.services.course import generate_course  # noqa: E402
from BE.utils.config import get_settings  # noqa: E402

st.set_page_config(
    page_title="LocalMuse AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    settings = get_settings()

    st.title("LocalMuse AI")
    st.caption(
        "AI가 취향과 현재 상황을 분석해 로컬 여행 코스를 추천합니다."
    )

    with st.sidebar:
        st.header("여행 조건")
        location = st.text_input(
            "현재 위치 / 지역",
            value=settings.default_region,
            help="위치 권한 거부 시 기본값: 서울 (PRD)",
        )
        purpose = st.text_area(
            "여행 목적 (자연어)",
            placeholder="예) 성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.",
            height=100,
        )
        time_budget = st.text_input("이용 가능 시간", value="3시간")
        transport = st.selectbox(
            "이동수단",
            options=["도보", "대중교통", "자동차", "자전거"],
            index=0,
        )
        submitted = st.button("코스 추천 받기", type="primary", use_container_width=True)

    if not submitted:
        st.info(
            "왼쪽에서 위치·목적·시간·이동수단을 입력한 뒤 "
            "**코스 추천 받기**를 눌러 주세요."
        )
        st.markdown(
            """
### Demo 시나리오 (PRD)
1. 현재 위치 허용 (또는 지역 입력)
2. 예: *성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.*
3. TourAPI 후보 → CLOVA 코스/이유 → 네이버 지도 동선
"""
        )
        return

    if not purpose.strip():
        st.warning("여행 목적을 입력해 주세요. (FR-01 자연어 입력)")
        return

    with st.spinner("AI가 여행 코스를 생성하고 있습니다…"):
        result = generate_course(
            location=location,
            purpose=purpose.strip(),
            time=time_budget,
            transport=transport,
        )

    st.subheader(result.get("title") or "추천 코스")
    if result.get("story"):
        st.markdown(f"**지역 스토리**  \n{result['story']}")

    places = result.get("places") or []
    if not places:
        st.error(result.get("message") or "코스를 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.")
        return

    for i, place in enumerate(places, start=1):
        with st.container(border=True):
            st.markdown(f"### {i}. {place.get('name', '장소')}")
            cols = st.columns(3)
            cols[0].write(f"**카테고리:** {place.get('category', '-')}")
            cols[1].write(f"**예상 체류:** {place.get('duration', '-')}")
            cols[2].write(f"**이동:** {place.get('travel_time', '-')}")
            if place.get("address"):
                st.caption(place["address"])
            if place.get("reason"):
                st.write(place["reason"])

    st.divider()
    st.markdown("#### 지도")
    st.info(
        "NAVER Maps Marker / Polyline 연동은 `BE/services/maps.py` 구현 후 "
        "이 영역에 임베드합니다. 지도 실패 시 위 텍스트 추천만 제공합니다. (PRD)"
    )
    if result.get("route_note"):
        st.caption(result["route_note"])


if __name__ == "__main__":
    main()
