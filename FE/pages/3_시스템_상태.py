"""시스템 / 연동 상태 점검 페이지."""

from __future__ import annotations

import streamlit as st

from FE.lib.bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from BE.services.health import get_health  # noqa: E402
from FE.components.styles import inject_styles  # noqa: E402

st.set_page_config(page_title="시스템 상태 · LocalMuse", page_icon="🩺", layout="wide")
inject_styles()

st.title("🩺 시스템 상태")
st.caption("환경변수 · DB · 외부 API 설정 여부 (키 값은 표시하지 않음)")

if st.button("상태 새로고침", type="primary"):
    st.cache_data.clear()

health = get_health()

c1, c2, c3, c4 = st.columns(4)
c1.metric("App env", health["app_env"])
c2.metric("DB", "OK" if health["db_ok"] else "FAIL")
c3.metric("Stub mode", "ON" if health["allow_stub"] else "OFF")
c4.metric("Default region", health["default_region"])

st.subheader("연동 설정")
st.dataframe(health["services"], use_container_width=True, hide_index=True)

st.subheader("요약")
for line in health["summary"]:
    st.write(f"- {line}")
