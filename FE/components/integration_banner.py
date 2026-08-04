"""홈 상단 연동 상태 배너 (키 값은 표시하지 않음)."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_integration_banner(health: dict[str, Any]) -> None:
    readiness = health.get("readiness") or "partial"
    services = {s["service"]: s for s in health.get("services") or []}

    def mark(name: str) -> str:
        s = services.get(name) or {}
        return "✅" if s.get("configured") else "⚪"

    line = (
        f"{mark('TourAPI')} TourAPI · "
        f"{mark('CLOVA Studio')} CLOVA · "
        f"{mark('NAVER Maps')} Maps · "
        f"{'✅' if health.get('db_ok') else '⚠️'} DB"
    )

    if readiness == "ready":
        st.success(f"실연동 준비 완료 — {line}")
    elif readiness == "demo_stub":
        st.warning(
            f"스텁/데모 모드 — 일부 API 키 미설정. {line}  \n"
            "키를 `.env`에 넣으면 실제 TourAPI·CLOVA·Maps 가 사용됩니다. "
            "자세한 안내: 사이드바 **시스템 상태**"
        )
    else:
        st.info(f"연동 상태 — {line}")
