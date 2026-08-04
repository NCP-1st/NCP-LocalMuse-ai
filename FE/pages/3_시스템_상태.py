"""시스템 / 연동 상태 점검 + probe. 선형 SVG 아이콘."""

from __future__ import annotations

import streamlit as st

from FE.lib.bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from BE.services.e2e import run_seongsu_e2e  # noqa: E402
from BE.services.health import get_health  # noqa: E402
from FE.components.icons import icon_heading  # noqa: E402
from FE.components.styles import inject_styles  # noqa: E402

st.set_page_config(
    page_title="시스템 상태 · LocalMuse",
    page_icon=None,
    layout="wide",
)
inject_styles()

st.markdown(
    icon_heading("activity", "시스템 상태", level=1, size=26),
    unsafe_allow_html=True,
)
st.caption("환경변수 · DB · 외부 API (키 값은 표시하지 않음)")

probe = st.checkbox("실호출 스모크 포함 (probe)", value=True)
cols = st.columns(2)
refresh = cols[0].button("상태 새로고침", type="primary")
run_e2e = cols[1].button("성수 E2E 실행 (A1)")

if refresh:
    st.cache_data.clear()

health = get_health(probe=probe)

c1, c2, c3, c4 = st.columns(4)
c1.metric("App env", health["app_env"])
c2.metric("DB", "OK" if health["db_ok"] else "FAIL")
c3.metric("Readiness", health.get("readiness", "-"))
c4.metric("Stub mode", "ON" if health["allow_stub"] else "OFF")

st.subheader("연동 설정")
st.dataframe(health["services"], use_container_width=True, hide_index=True)

if health.get("probes"):
    st.subheader("실호출 스모크 (probe)")
    st.dataframe(health["probes"], use_container_width=True, hide_index=True)

st.subheader("요약")
for line in health["summary"]:
    st.write(f"- {line}")

st.subheader("설정 가이드")
for h in health.get("setup_hints") or []:
    st.write(f"- {h}")

st.code(
    "cp .env.example .env\n"
    "# TOUR_API_KEY, CLOVA_API_KEY, NAVER_MAP_CLIENT_ID, NAVER_MAP_CLIENT_SECRET\n"
    "python -m BE health --probe\n"
    "python -m BE e2e",
    language="bash",
)

if run_e2e:
    st.subheader("성수 E2E 결과")
    with st.spinner("probe + 성수 코스 생성 중…"):
        report = run_seongsu_e2e(save=False, probe=True)
    verdict = report.get("verdict") or {}
    if verdict.get("live_demo_ok"):
        st.success(verdict.get("message"))
    elif verdict.get("demo_ok"):
        st.warning(verdict.get("message"))
    else:
        st.error(verdict.get("message"))
    st.json(
        {
            "verdict": verdict,
            "course": report.get("course"),
            "probes": (report.get("health") or {}).get("probes"),
        }
    )
