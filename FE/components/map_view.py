"""
지도 영역 — NAVER Dynamic Map(JS) only.

좌표: TourAPI mapx/mapy (Geocode REST 미사용)
인증: Client ID + Web 서비스 URL (http://localhost 포트 없이)
실패 시: st.map 폴백 또는 텍스트 동선
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

    st.caption(
        "좌표: TourAPI · 지도: NAVER Dynamic Map (Geocode REST 미사용)"
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
    client_id = (
        naver_client_id
        or route.get("naver_client_id")
        or None
    )
    if isinstance(client_id, str):
        client_id = client_id.strip() or None

    if not rows and not current:
        st.info("마커 좌표가 없습니다. 텍스트 동선만 확인하세요.")
        return

    if client_id and rows:
        st.markdown(
            f'{icon("check-circle", size=14, class_name="lm-icon lm-icon-ok")} '
            f"<span>NAVER Dynamic Map · 마커 {len(rows)}개 · Polyline "
            f"(좌표 출처: TourAPI)</span>",
            unsafe_allow_html=True,
        )
        with st.expander("지도 인증이 실패하면", expanded=False):
            st.markdown(
                """
1. NCP Application **Web 서비스 URL** 에 포트 **없이** 등록  
   - `http://localhost`  
   - `http://127.0.0.1`  
2. **Dynamic Map** 체크  
3. Client ID = `.env` 의 `NAVER_MAP_CLIENT_ID`  
4. 브라우저 주소는 `http://localhost:8501` (등록 URL은 포트 없음)  
5. 강력 새로고침 후 재시도  
"""
            )
        _render_naver_maps(rows, client_id=client_id, current=current)
    elif rows:
        st.markdown(
            f'{icon("alert", size=14, class_name="lm-icon lm-icon-warn")} '
            f"<span>Client ID 없음 — Streamlit 기본 지도 폴백</span>",
            unsafe_allow_html=True,
        )
        df = pd.DataFrame(rows)
        st.map(df[["lat", "lon"]], size=40)
    else:
        st.info("표시할 장소 좌표가 없습니다.")

    if rows:
        with st.expander("장소 좌표 목록 (TourAPI)", expanded=False):
            st.dataframe(
                pd.DataFrame(rows)[["order", "name", "category", "address", "lat", "lon"]],
                hide_index=True,
                use_container_width=True,
            )


def _render_naver_maps(
    rows: list[dict[str, Any]],
    *,
    client_id: str,
    current: dict[str, float] | None = None,
) -> None:
    """NAVER Dynamic Map v3: 번호 마커 + Polyline + fitBounds."""
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
    cid = escape(client_id)

    # ncpKeyId = Application Client ID (Dynamic Map)
    # 인증 실패 시 안내 HTML 표시
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    html, body {{ margin:0; padding:0; height:100%; background:#f4f6f8; font-family:-apple-system,BlinkMacSystemFont,sans-serif; }}
    #nmap {{ width:100%; height:480px; border-radius:12px; }}
    .nm-label {{
      background:#2F6FED; color:#fff; border-radius:999px;
      width:26px; height:26px; display:flex; align-items:center; justify-content:center;
      font: 700 12px/1 sans-serif; border:2px solid #fff;
      box-shadow:0 1px 4px rgba(0,0,0,.28);
    }}
    .nm-label.cur {{ background:#c0392b; width:auto; padding:0 6px; font-size:10px; }}
    .nm-err {{
      padding:16px 18px; color:#5c1a1a; background:#fdecec; border-radius:12px;
      font-size:13px; line-height:1.5;
    }}
    .nm-err code {{ background:#fff; padding:1px 4px; border-radius:4px; }}
  </style>
</head>
<body>
  <div id="nmap"></div>
  <script>
    window.navermap_authFailure = function () {{
      var el = document.getElementById('nmap');
      if (!el) return;
      el.innerHTML = '<div class="nm-err">'
        + '<b>NAVER Dynamic Map 인증 실패</b><br/>'
        + '1) NCP Application → Web 서비스 URL 에 <code>http://localhost</code> '
        + '(포트 없이) 등록<br/>'
        + '2) <code>http://127.0.0.1</code> 도 추가<br/>'
        + '3) Dynamic Map 사용 체크 · Client ID 일치<br/>'
        + '4) 브라우저 주소가 localhost 인지 확인 후 강력 새로고침'
        + '</div>';
    }};
  </script>
  <script type="text/javascript"
    src="https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId={cid}"
    onerror="document.getElementById('nmap').innerHTML='<div class=nm-err>Maps JS 스크립트 로드 실패. 네트워크 또는 Client ID 를 확인하세요.</div>'"></script>
  <script>
    (function() {{
      if (typeof naver === 'undefined' || !naver.maps) {{
        // authFailure 가 이미 그렸을 수 있음
        var el = document.getElementById('nmap');
        if (el && !el.querySelector('.nm-err')) {{
          el.innerHTML = '<div class="nm-err">NAVER Maps 객체를 사용할 수 없습니다. '
            + 'Client ID / Web 서비스 URL(http://localhost) 을 확인하세요.</div>';
        }}
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
            anchor: new naver.maps.Point(16, 13)
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
