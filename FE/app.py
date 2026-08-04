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
from BE.services.health import get_health  # noqa: E402
from BE.utils.config import get_settings  # noqa: E402
from FE.components import (  # noqa: E402
    inject_styles,
    render_course_result,
    render_hero,
    render_sidebar_form,
)
from FE.components.integration_banner import render_integration_banner  # noqa: E402
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

    health = get_health(probe=False)
    render_integration_banner(health)

    form = render_sidebar_form(
        default_region=settings.default_region,
        default_nickname=session.get_nickname(),
    )
    session.set_nickname(form.nickname)

    if not form.submitted and not session.get_result():
        st.info(
            "왼쪽에서 위치·목적·시간·이동수단을 입력하거나, "
            "**데모 원클릭**으로 PRD 시나리오를 바로 실행하세요."
        )
        _render_empty_guide()
        return

    if form.submitted:
        if not form.purpose:
            st.warning("여행 목적을 입력해 주세요. (FR-01 자연어 입력)")
            return

        if form.is_demo:
            st.toast("PRD 데모 시나리오 실행 중…", icon="⚡")

        user_id = None
        try:
            user_id = repo.ensure_user(form.nickname)
        except Exception:
            pass

        result = _run_with_stages(
            location=form.location,
            purpose=form.purpose,
            time=form.time,
            transport=form.transport,
            user_id=user_id,
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
        client_id = settings.naver_map_client_id or settings.naver_openapi_client_id
        render_course_result(result, naver_client_id=client_id or None)
        _render_pipeline_meta(result)


def _run_with_stages(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    user_id: int | None,
) -> dict:
    """단계별 로딩 UI (TourAPI → CLOVA → Maps → 저장)."""
    stage_labels = {
        "tourapi": "① TourAPI — 관광 장소 후보 수집",
        "clova": "② CLOVA Studio — 코스·추천 이유·스토리",
        "maps": "③ Maps — 좌표 보강·동선 구성",
        "save": "④ DB — 코스 저장",
        "done": "✅ 완료",
    }

    with st.status("여행 코스 생성 중…", expanded=True) as status:
        lines: list[str] = []

        def on_stage(name: str, payload: dict) -> None:
            label = stage_labels.get(name, name)
            msg = payload.get("message") or payload.get("status") or ""
            line = f"**{label}** — {msg}"
            lines.append(line)
            # status 컨테이너에 누적 표시
            status.update(label=f"진행 중: {label}", state="running")
            st.write(line)

        result = generate_course(
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
            user_id=user_id,
            save=True,
            on_stage=on_stage,
        )

        elapsed = result.get("elapsed_ms")
        if result.get("places"):
            status.update(
                label=f"완료 ({elapsed}ms)" if elapsed else "완료",
                state="complete",
            )
        else:
            status.update(
                label=result.get("message") or "실패",
                state="error",
            )

    return result


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
    elapsed = result.get("elapsed_ms")
    if elapsed is not None:
        st.caption(f"생성 소요: {elapsed} ms · 후보 {result.get('candidates_count', 0)}곳")


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
1. 사이드바 **「성수 3시간 · 감성 카페+산책」** 원클릭  
   또는 직접 입력: *성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.*
2. 단계 표시: TourAPI → CLOVA → Maps → 저장
3. 장소 카드 + 지도 동선 확인
"""
    )


if __name__ == "__main__":
    main()
