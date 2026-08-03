"""
LocalMuse AI — Streamlit Frontend entrypoint.

PRD User Flow:
  Start → 현재 위치 허용 → 여행 목적 입력 → AI 요청
       → 코스 생성 → 지도 출력 → 장소 상세 확인 → 종료
"""

from __future__ import annotations

import streamlit as st

from FE.lib.bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from BE.database import repository as repo  # noqa: E402
from BE.services.course import generate_course  # noqa: E402
from BE.utils.config import get_settings  # noqa: E402
from FE.components import (  # noqa: E402
    inject_styles,
    render_course_result,
    render_hero,
    render_sidebar_form,
)
from FE.lib import session  # noqa: E402

st.set_page_config(
    page_title="LocalMuse AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    inject_styles()
    settings = get_settings()
    render_hero()

    form = render_sidebar_form(
        default_region=settings.default_region,
        default_nickname=session.get_nickname(),
    )
    session.set_nickname(form.nickname)

    # 빈 화면 안내
    if not form.submitted and not session.get_result():
        st.info(
            "왼쪽에서 위치·목적·시간·이동수단을 입력한 뒤 "
            "**코스 추천 받기**를 눌러 주세요."
        )
        _render_empty_guide()
        return

    if form.submitted:
        if not form.purpose:
            st.warning("여행 목적을 입력해 주세요. (FR-01 자연어 입력)")
            return

        user_id = None
        try:
            user_id = repo.ensure_user(form.nickname)
        except Exception:
            # 저장 실패해도 추천은 진행
            pass

        with st.spinner("AI가 여행 코스를 생성하고 있습니다… (TourAPI → CLOVA → Maps)"):
            result = generate_course(
                location=form.location,
                purpose=form.purpose,
                time=form.time,
                transport=form.transport,
                user_id=user_id,
                save=True,
            )

        session.set_result(
            result,
            query={
                "location": form.location,
                "purpose": form.purpose,
                "time": form.time,
                "transport": form.transport,
                "nickname": form.nickname,
            },
        )

    result = session.get_result()
    if result:
        client_id = settings.naver_map_client_id or settings.naver_openapi_client_id
        render_course_result(result, naver_client_id=client_id or None)


def _render_empty_guide() -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("##### ① 조건 입력")
        st.write("위치 · 자연어 목적 · 시간 · 이동수단")
    with c2:
        st.markdown("##### ② AI 코스")
        st.write("TourAPI 후보 + CLOVA 추천 이유 · 스토리")
    with c3:
        st.markdown("##### ③ 지도 동선")
        st.write("Marker · Polyline · 장소 상세")

    st.divider()
    st.markdown(
        """
### Demo 시나리오 (PRD)
1. 현재 위치 허용 (또는 지역 입력: **성수**)
2. 입력 예: *성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.*
3. TourAPI 후보 → CLOVA 코스/이유 → 지도 동선 확인
"""
    )


if __name__ == "__main__":
    main()
