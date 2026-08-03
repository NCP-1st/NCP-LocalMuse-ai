"""Streamlit session_state 키 관리."""

from __future__ import annotations

from typing import Any

import streamlit as st

KEY_LAST_RESULT = "last_course_result"
KEY_LAST_QUERY = "last_course_query"
KEY_NICKNAME = "nickname"


def get_result() -> dict[str, Any] | None:
    return st.session_state.get(KEY_LAST_RESULT)


def set_result(result: dict[str, Any], query: dict[str, Any] | None = None) -> None:
    st.session_state[KEY_LAST_RESULT] = result
    if query is not None:
        st.session_state[KEY_LAST_QUERY] = query


def get_query() -> dict[str, Any] | None:
    return st.session_state.get(KEY_LAST_QUERY)


def get_nickname(default: str = "guest") -> str:
    return str(st.session_state.get(KEY_NICKNAME) or default)


def set_nickname(name: str) -> None:
    st.session_state[KEY_NICKNAME] = name.strip() or "guest"
