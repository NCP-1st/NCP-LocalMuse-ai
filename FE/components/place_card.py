"""장소 카드 (FR-04 장소 상세). 선형 SVG 아이콘."""

from __future__ import annotations

from typing import Any

import streamlit as st

from FE.components.icons import icon_text


def render_place_card(index: int, place: dict[str, Any]) -> None:
    name = place.get("name") or f"장소 {index}"
    category = place.get("category") or "-"
    duration = place.get("duration") or "-"
    travel = place.get("travel_time") or "-"
    address = place.get("address") or ""
    reason = place.get("reason") or ""
    image = place.get("image")

    with st.container(border=True):
        cols = st.columns([3, 1] if image else [1])
        with cols[0]:
            st.markdown(f"### {index}. {name}")
            st.markdown(
                f'<span class="lm-badge">{category}</span>'
                f'<span class="lm-badge">체류 {duration}</span>'
                f'<span class="lm-badge">이동 {travel}</span>',
                unsafe_allow_html=True,
            )
            if address:
                st.markdown(icon_text("map-pin", address, size=14), unsafe_allow_html=True)
            if reason:
                st.write(reason)
            lat, lng = place.get("latitude"), place.get("longitude")
            if lat is not None and lng is not None:
                st.caption(f"좌표: {float(lat):.5f}, {float(lng):.5f}")
        if image and len(cols) > 1:
            with cols[1]:
                try:
                    st.image(image, use_container_width=True)
                except Exception:
                    pass
