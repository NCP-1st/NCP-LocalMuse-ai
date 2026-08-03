"""CSS 로드."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_CSS = Path(__file__).resolve().parent.parent / "assets" / "styles.css"


def inject_styles() -> None:
    if _CSS.exists():
        st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
