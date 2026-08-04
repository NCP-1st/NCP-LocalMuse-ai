"""실데이터 vs 스텁 배지 (선형 SVG)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from FE.components.icons import icon


def render_live_badge(result: dict[str, Any], *, maps_js: bool) -> None:
    source = result.get("source")
    places = result.get("places") or []
    stub_n = sum(
        1 for p in places if str(p.get("content_id") or "").startswith("stub")
    )
    route = result.get("route") or {}
    markers = len(route.get("markers") or [])

    clova_live = source == "clova"
    tour_live = len(places) > 0 and stub_n == 0
    map_live = bool(route.get("available")) and maps_js

    bits = []
    bits.append(_bit("TourAPI", tour_live, f"stub {stub_n}" if stub_n else "live"))
    bits.append(_bit("CLOVA", clova_live, source or "-"))
    bits.append(
        _bit(
            "Maps",
            map_live,
            f"naver_js · {markers} markers"
            if map_live
            else ("st_map/text" if route.get("available") else "no coords"),
        )
    )

    st.markdown(
        '<div class="lm-icon-row" style="flex-wrap:wrap;gap:0.75rem;margin:0.5rem 0 1rem 0">'
        + "".join(bits)
        + "</div>",
        unsafe_allow_html=True,
    )

    if clova_live and tour_live and map_live:
        st.success("실데이터 데모 모드 — TourAPI + CLOVA + NAVER Maps")
    elif clova_live and tour_live:
        st.info(
            "TourAPI·CLOVA 실연동. 지도는 Client ID 설정 시 NAVER Maps 로 표시됩니다."
        )
    else:
        st.caption(
            "스텁/부분 연동일 수 있습니다. `.env` 키와 `python -m BE e2e` 결과를 확인하세요."
        )


def _bit(label: str, ok: bool, detail: str) -> str:
    ic = (
        icon("check-circle", size=14, class_name="lm-icon lm-icon-ok")
        if ok
        else icon("circle", size=14, class_name="lm-icon lm-icon-muted")
    )
    return (
        f'<span class="lm-badge" style="display:inline-flex;align-items:center;gap:0.3rem">'
        f"{ic} {label}: {detail}</span>"
    )
