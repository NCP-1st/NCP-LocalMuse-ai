"""
지도 영역. 선형 SVG 아이콘 사용 (이모지 금지).

PRD: NAVER Maps Marker / Polyline / 현재 위치.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from FE.components.icons import icon, icon_heading


def render_map(
    route: dict[str, Any] | None,
    *,
    route_note: str | None = None,
    naver_client_id: str | None = None,
) -> None:
    st.markdown(
        icon_heading("map", "지도 · 이동 동선", level=3, size=20),
        unsafe_allow_html=True,
    )

    if route_note:
        st.markdown(
            f'<div class="lm-route">{icon("route", size=16)} '
            f"<span>{route_note}</span></div>",
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
            "order": int(m.get("order") or (i + 1)),
            "category": m.get("category") or "",
        }
        for i, m in enumerate(markers)
        if m.get("lat") is not None and m.get("lng") is not None
    ]

    current = route.get("current")
    if not rows and not current:
        st.info("마커 좌표가 없습니다. 텍스트 동선만 확인하세요.")
        return

    if naver_client_id and rows:
        _render_naver_maps(rows, client_id=naver_client_id, current=current)
    elif rows:
        st.caption(
            "NAVER_MAP_CLIENT_ID 미설정 — 기본 지도(st.map) 폴백. "
            "Marker 번호·Polyline 은 Client ID 설정 후 활성화됩니다."
        )
        df = pd.DataFrame(rows)
        st.map(df[["lat", "lon"]], size=40)
    else:
        st.info("표시할 장소 좌표가 없습니다.")

    if rows:
        with st.expander("장소 좌표 목록", expanded=False):
            st.dataframe(
                pd.DataFrame(rows)[["order", "name", "category", "lat", "lon"]],
                hide_index=True,
                use_container_width=True,
            )


def _render_naver_maps(
    rows: list[dict[str, Any]],
    *,
    client_id: str,
    current: dict[str, float] | None = None,
) -> None:
    """NAVER Maps: 번호 마커 + Polyline + 현재 위치 + bounds."""
    center_lat = sum(r["lat"] for r in rows) / len(rows)
    center_lng = sum(r["lon"] for r in rows) / len(rows)

    points = [
        {"lat": r["lat"], "lng": r["lon"], "name": r["name"], "order": r["order"]}
        for r in rows
    ]
    points_json = json.dumps(points, ensure_ascii=False)
    current_json = json.dumps(current, ensure_ascii=False) if current else "null"

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    html, body {{ margin:0; padding:0; height:100%; }}
    #nmap {{ width:100%; height:460px; border-radius:12px; }}
    .nm-label {{
      background:#2F6FED; color:#fff; border-radius:999px;
      width:24px; height:24px; display:flex; align-items:center; justify-content:center;
      font: 700 12px/1 sans-serif; border:2px solid #fff;
      box-shadow:0 1px 4px rgba(0,0,0,.25);
    }}
    .nm-label.cur {{ background:#e74c3c; font-size:10px; }}
  </style>
</head>
<body>
  <div id="nmap"></div>
  <script src="https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId={client_id}"></script>
  <script>
    (function() {{
      var points = {points_json};
      var current = {current_json};
      var map = new naver.maps.Map('nmap', {{
        center: new naver.maps.LatLng({center_lat}, {center_lng}),
        zoom: 14,
        zoomControl: true,
        zoomControlOptions: {{ position: naver.maps.Position.TOP_RIGHT }}
      }});

      var bounds = new naver.maps.LatLngBounds();
      var path = [];

      if (current && current.latitude != null && current.longitude != null) {{
        var curLatLng = new naver.maps.LatLng(current.latitude, current.longitude);
        path.push(curLatLng);
        bounds.extend(curLatLng);
        new naver.maps.Marker({{
          position: curLatLng,
          map: map,
          title: '현재 위치',
          icon: {{
            content: '<div class="nm-label cur">C</div>',
            anchor: new naver.maps.Point(12, 12)
          }}
        }});
      }}

      points.forEach(function(p) {{
        var latlng = new naver.maps.LatLng(p.lat, p.lng);
        path.push(latlng);
        bounds.extend(latlng);
        new naver.maps.Marker({{
          position: latlng,
          map: map,
          title: p.name,
          icon: {{
            content: '<div class="nm-label">' + p.order + '</div>',
            anchor: new naver.maps.Point(12, 12)
          }}
        }});
      }});

      if (path.length > 1) {{
        new naver.maps.Polyline({{
          map: map,
          path: path,
          strokeColor: '#2F6FED',
          strokeWeight: 4,
          strokeOpacity: 0.85,
          strokeStyle: 'solid'
        }});
      }}

      if (points.length > 0) {{
        map.fitBounds(bounds, {{ top: 40, right: 40, bottom: 40, left: 40 }});
      }}
    }})();
  </script>
</body>
</html>
"""
    st.markdown(
        f'{icon("map", size=16)} <strong>NAVER Maps</strong>',
        unsafe_allow_html=True,
    )
    components.html(html, height=480, scrolling=False)
