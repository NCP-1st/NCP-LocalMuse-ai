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
from BE.services.health import get_health  # noqa: E402
from BE.utils.config import get_settings  # noqa: E402
from FE.components import (  # noqa: E402
    inject_styles,
    render_course_result,
    render_hero,
    render_sidebar_form,
)
from FE.components.demo_panel import render_demo_panel  # noqa: E402
from FE.components.integration_banner import render_integration_banner  # noqa: E402
from FE.components.pipeline_status import (  # noqa: E402
    render_stage_timeline,
    run_course_with_stage_ui,
)
from FE.lib import session  # noqa: E402

st.set_page_config(
    page_title="LocalMuse AI",
    # 이모지 page_icon 사용 금지 — 선형 SVG 는 본문 icons 모듈 사용
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    inject_styles()
    settings = get_settings()
    render_hero()

    health = get_health(probe=False)
    render_integration_banner(health)

    form = render_sidebar_form(
        default_region=settings.default_region,
        default_nickname=session.get_nickname(),
    )
    session.set_nickname(form.nickname)

    if not form.submitted and not session.get_result():
        st.info(
            "왼쪽에서 조건을 입력하거나, 아래 **데모 원클릭**으로 "
            "PRD 시나리오를 바로 실행하세요."
        )
        render_demo_panel()
        st.divider()
        _render_empty_guide()
        return

    if form.submitted:
        if not form.purpose:
            st.warning("여행 목적을 입력해 주세요. (FR-01 자연어 입력)")
            return

        if form.is_demo:
            from FE.components.icons import icon_text

            # toast icon 슬롯은 이모지 전용 → 생략, 본문에 선형 SVG 사용
            st.toast("PRD 데모 시나리오 실행 중…")
            st.markdown(
                f"{icon_text('zap', '데모 실행')} · "
                f"{form.location} · {form.time} · {form.transport}",
                unsafe_allow_html=True,
            )
            st.caption(form.purpose)

        user_id = None
        try:
            user_id = repo.ensure_user(form.nickname)
        except Exception:
            pass

        result = run_course_with_stage_ui(
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
                "is_demo": form.is_demo,
            },
        )

    result = session.get_result()
    if result:
        # 다시 데모 / 새 추천
        with st.sidebar:
            if st.button("새 추천 시작 (결과 초기화)", use_container_width=True):
                session.clear_result()
                st.rerun()

        client_id = settings.naver_map_client_id or settings.naver_openapi_client_id
        render_course_result(result, naver_client_id=client_id or None)
        _render_pipeline_meta(result)
        render_stage_timeline(result)


def _render_pipeline_meta(result: dict) -> None:
    source = result.get("source")
    if source == "fallback":
        st.warning(
            "AI(CLOVA) 대신 **fallback 코스**가 사용되었습니다. "
            "`.env`의 `CLOVA_API_KEY`를 확인하거나, 잠시 후 다시 시도해 주세요."
            + (
                f" ({result.get('fallback_note')})"
                if result.get("fallback_note")
                else ""
            )
        )
    quality = result.get("quality") or {}
    if quality:
        st.caption(
            f"품질 점수: {quality.get('score', '-')} / 100 · "
            f"이유 있는 장소 {quality.get('with_reason', 0)}/"
            f"{quality.get('place_count', 0)}"
        )
    elapsed = result.get("elapsed_ms")
    if elapsed is not None:
        st.caption(
            f"생성 소요: {elapsed} ms · 후보 {result.get('candidates_count', 0)}곳"
        )


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
1. **「지금 데모 실행」** 또는 사이드바 **성수 3시간 · 감성 카페+산책**
2. 단계 표시: TourAPI → CLOVA → Maps → 저장 (progress bar)
3. 장소 카드 + 지도 동선 + 파이프라인 로그 확인
"""
    )


if __name__ == "__main__":
    main()
