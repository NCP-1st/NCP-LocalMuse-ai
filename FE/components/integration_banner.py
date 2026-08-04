"""홈 상단 연동 상태 배너 (키 값은 표시하지 않음). 선형 SVG 아이콘만 사용."""

from __future__ import annotations

from typing import Any

import streamlit as st

from FE.components.icons import status_icon, warn_icon


def render_integration_banner(health: dict[str, Any]) -> None:
    readiness = health.get("readiness") or "partial"
    services = {s["service"]: s for s in health.get("services") or []}

    def mark(name: str) -> str:
        s = services.get(name) or {}
        return status_icon(bool(s.get("configured")))

    db_mark = status_icon(bool(health.get("db_ok"))) if health.get("db_ok") else warn_icon()

    line = (
        f"{mark('TourAPI')} TourAPI · "
        f"{mark('CLOVA Studio')} CLOVA · "
        f"{mark('NAVER Maps')} Maps · "
        f"{db_mark} DB"
    )

    if readiness == "ready":
        st.success("실연동 준비 완료")
        st.markdown(line, unsafe_allow_html=True)
    elif readiness == "demo_stub":
        st.warning(
            "스텁/데모 모드 — 일부 API 키 미설정. "
            "키를 `.env`에 넣으면 실제 TourAPI·CLOVA·Maps 가 사용됩니다. "
            "자세한 안내: 사이드바 **시스템 상태**"
        )
        st.markdown(line, unsafe_allow_html=True)
    else:
        st.info("연동 상태")
        st.markdown(line, unsafe_allow_html=True)
