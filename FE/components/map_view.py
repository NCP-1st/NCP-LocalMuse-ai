"""
지도 영역 — A3 NAVER Maps 실화면.

우선순위:
  1) Client ID + 좌표 → NAVER Maps JS (번호 Marker + Polyline + fitBounds)
  2) 좌표만 → st.map 폴백
  3) 좌표 없음 → 텍스트 동선 (PRD)
"""

from __future__ import annotations

import json
from html import escape
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
            f"<span>{escape(str(route_note))}</span></div>",
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
            "name": str(m.get("name") or ""),
            "order": int(m.get("order") or (i + 1)),
            "category": str(m.get("category") or ""),
            "address": str(m.get("address") or ""),
        }
        for i, m in enumerate(markers)
        if m.get("lat") is not None and m.get("lng") is not None
    ]

    current = route.get("current")
    if not rows and not current:
        st.info("마커 좌표가 없습니다. 텍스트 동선만 확인하세요.")
        return

    use_naver = bool(naver_client_id and rows)
    if use_naver:
        st.markdown(
            f'{icon("check-circle", size=14, class_name="lm-icon lm-icon-ok")} '
            f"<span>NAVER Maps · 마커 {len(rows)}개 · Polyline</span>",
            unsafe_allow_html=True,
        )
        _render_naver_maps(rows, client_id=naver_client_id, current=current)
    elif rows:
        st.markdown(
            f'{icon("alert", size=14, class_name="lm-icon lm-icon-warn")} '
            f"<span>NAVER_MAP_CLIENT_ID 미설정 — 기본 지도(st.map) 폴백</span>",
            unsafe_allow_html=True,
        )
        df = pd.DataFrame(rows)
        st.map(df[["lat", "lon"]], size=40)
    else:
        st.info("표시할 장소 좌표가 없습니다.")

    if rows:
        with st.expander("장소 좌표 목록", expanded=False):
            st.dataframe(
                pd.DataFrame(rows)[
                    [c for c in ["order", "name", "category", "address", "lat", "lon"] if c in rows[0] or c in ("order", "name", "lat", "lon")]
                ],
                hide_index=True,
                use_container_width=True,
            )


def _render_naver_maps(
    rows: list[dict[str, Any]],
    *,
    client_id: str,
    current: dict[str, float] | None = None,
) -> None:
    """NAVER Dynamic Map: 번호 마커 + Polyline + fitBounds."""
    center_lat = sum(r["lat"] for r in rows) / len(rows)
    center_lng = sum(r["lon"] for r in rows) / len(rows)

    points = [
        {
            "lat": r["lat"],
            "lng": r["lon"],
            "name": r["name"],
            "order": r["order"],
            "category": r.get("category") or "",
        }
        for r in rows
    ]
    points_json = json.dumps(points, ensure_ascii=False)
    current_json = json.dumps(current, ensure_ascii=False) if current else "null"
    # escape client id for HTML attr
    cid = escape(client_id)

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    html, body {{ margin:0; padding:0; height:100%; background:#f4f6f8; }}
    #nmap {{ width:100%; height:480px; border-radius:12px; }}
    .nm-label {{
      background:#2F6FED; color:#fff; border-radius:999px;
      width:26px; height:26px; display:flex; align-items:center; justify-content:center;
      font: 700 12px/1 -apple-system, BlinkMacSystemFont, sans-serif;
      border:2px solid #fff; box-shadow:0 1px 4px rgba(0,0,0,.28);
    }}
    .nm-label.cur {{
      background:#c0392b; width:28px; height:28px; font-size:10px; letter-spacing:-0.02em;
    }}
    .nm-err {{
      padding:16px; font:14px/1.4 sans-serif; color:#7a1f1f; background:#fdecec;
      border-radius:12px;
    }}
  </style>
</head>
<body>
  <div id="nmap"></div>
  <script>
    window.onerror = function(msg) {{
      var el = document.getElementById('nmap');
      if (el) el.innerHTML = '<div class="nm-err">Maps load error: ' + msg +
        '<br/>Client ID / 도메인 등록(NCP Maps)을 확인하세요.</div>';
    }};
  </script>
  <script src="https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId={cid}"
    onerror="document.getElementById('nmap').innerHTML='<div class=nm-err>NAVER Maps JS 로드 실패. NAVER_MAP_CLIENT_ID 와 Web 서비스 URL 등록을 확인하세요.</div>'"></script>
  <script>
    (function() {{
      if (typeof naver === 'undefined' || !naver.maps) {{
        document.getElementById('nmap').innerHTML =
          '<div class="nm-err">NAVER Maps 객체를 사용할 수 없습니다. Client ID / 허용 URL 설정을 확인하세요.</div>';
        return;
      }}
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
            content: '<div class="nm-label cur">NOW</div>',
            anchor: new naver.maps.Point(14, 14)
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
            anchor: new naver.maps.Point(13, 13)
          }}
        }});
      }});

      if (path.length > 1) {{
        new naver.maps.Polyline({{
          map: map,
          path: path,
          strokeColor: '#2F6FED',
          strokeWeight: 4,
          strokeOpacity: 0.88,
          strokeStyle: 'solid'
        }});
      }}

      if (points.length > 0) {{
        map.fitBounds(bounds, {{ top: 48, right: 48, bottom: 48, left: 48 }});
      }}
    }})();
  </script>
</body>
</html>
"""
    components.html(html, height=500, scrolling=False)
