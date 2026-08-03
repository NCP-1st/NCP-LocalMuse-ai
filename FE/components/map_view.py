"""
지도 영역.

PRD: NAVER Maps Marker / Polyline / 현재 위치.
- 좌표가 있으면 Streamlit `st.map` 으로 즉시 표시 (텍스트 폴백 방지)
- NAVER Maps JS 임베드는 Client ID 있을 때 HTML 컴포넌트로 확장 가능 (skeleton)
- 지도 데이터 없으면 텍스트 동선만 표시 (PRD Error Handling)
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render_map(
    route: dict[str, Any] | None,
    *,
    route_note: str | None = None,
    naver_client_id: str | None = None,
) -> None:
    st.subheader("지도 · 이동 동선")

    if route_note:
        st.markdown(
            f'<div class="lm-route">🗺 {route_note}</div>',
            unsafe_allow_html=True,
        )

    if not route or not route.get("available"):
        st.info(
            "표시할 좌표가 없어 텍스트 추천만 제공합니다. "
            "(지도 실패 시 폴백 — PRD)"
        )
        return

    markers = route.get("markers") or []
    rows = [
        {
            "lat": float(m["lat"]),
            "lon": float(m["lng"]),
            "name": m.get("name", ""),
            "order": m.get("order", i + 1),
        }
        for i, m in enumerate(markers)
        if m.get("lat") is not None and m.get("lng") is not None
    ]

    if not rows:
        st.info("마커 좌표가 없습니다. 텍스트 동선만 확인하세요.")
        return

    df = pd.DataFrame(rows)
    # Streamlit map: lat / lon 컬럼
    st.map(df[["lat", "lon"]], size=40)


    with st.expander("장소 좌표 목록", expanded=False):
        st.dataframe(
            df[["order", "name", "lat", "lon"]],
            hide_index=True,
            use_container_width=True,
        )

    if naver_client_id:
        _render_naver_maps_skeleton(rows, naver_client_id)
    else:
        st.caption(
            "NAVER Maps JS 임베드는 `NAVER_MAP_CLIENT_ID` 설정 후 활성화됩니다. "
            "현재는 좌표 기반 기본 지도를 표시합니다."
        )


def _render_naver_maps_skeleton(
    rows: list[dict[str, Any]],
    client_id: str,
) -> None:
    """NAVER Maps JavaScript API 임베드 뼈대 (MVP 확장 지점)."""
    if not rows:
        return

    center_lat = sum(r["lat"] for r in rows) / len(rows)
    center_lng = sum(r["lon"] for r in rows) / len(rows)
    path_js = ", ".join(
        f"new naver.maps.LatLng({r['lat']}, {r['lon']})" for r in rows
    )
    markers_js = "\n".join(
        f"""
        new naver.maps.Marker({{
          position: new naver.maps.LatLng({r['lat']}, {r['lon']}),
          map: map,
          title: {repr(r['name'])}
        }});
        """
        for r in rows
    )

    html = f"""
    <div id="nmap" style="width:100%;height:420px;border-radius:12px;"></div>
    <script type="text/javascript"
      src="https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId={client_id}"></script>
    <script>
      var map = new naver.maps.Map('nmap', {{
        center: new naver.maps.LatLng({center_lat}, {center_lng}),
        zoom: 14
      }});
      {markers_js}
      var path = [{path_js}];
      if (path.length > 1) {{
        new naver.maps.Polyline({{
          map: map,
          path: path,
          strokeColor: '#2F6FED',
          strokeWeight: 4,
          strokeOpacity: 0.8
        }});
      }}
    </script>
    """
    st.markdown("##### NAVER Maps")
    components.html(html, height=440)
