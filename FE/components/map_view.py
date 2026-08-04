"""
인터랙티브 코스 지도 (Leaflet).

요구사항:
  - 빨간 숫자 마커 (1,2,3,4…)
  - 지점 간 화살표 선 연결
  - 마커 클릭 시 장소 정보 팝업 (API 데이터)
  - 좌측 하단 루트 순서 패널
  - 좌표: TourAPI (Geocode 미사용)
"""

from __future__ import annotations

import json
from html import escape
from typing import Any
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from FE.components.icons import icon, icon_heading


def render_map(
    route: dict[str, Any] | None,
    *,
    route_note: str | None = None,
    naver_client_id: str | None = None,
    places: list[dict[str, Any]] | None = None,
) -> None:
    del naver_client_id  # Dynamic Map iframe 인증 이슈로 미사용

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
        "빨간 숫자 마커 · 화살표 동선 · 클릭 팝업 · 좌측 하단 루트 순서 "
        "(좌표: TourAPI)"
    )

    points = _build_points(route, places)
    if not points:
        st.info(
            "표시할 좌표가 없어 텍스트 추천만 제공합니다. "
            "(지도 실패 시 폴백 — PRD)"
        )
        if places:
            _render_text_route(places)
        return

    html = _leaflet_route_html(points)
    components.html(html, height=560, scrolling=False)

    # 네이버 지도 외부 링크 (보조)
    first = points[0]
    st.link_button(
        "네이버 지도에서 시작 지점 열기",
        f"https://map.naver.com/v5/?c={first['lng']},{first['lat']},15,0,0,0,dh",
        use_container_width=True,
    )


def _build_points(
    route: dict[str, Any] | None,
    places: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """route.markers + places 상세를 합쳐 팝업용 포인트 생성."""
    by_id: dict[str, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    if places:
        for p in places:
            if p.get("content_id") is not None:
                by_id[str(p["content_id"])] = p
            if p.get("name"):
                by_name[str(p["name"]).strip()] = p

    markers = (route or {}).get("markers") or []
    points: list[dict[str, Any]] = []

    if markers:
        for i, m in enumerate(markers, start=1):
            lat, lng = m.get("lat"), m.get("lng")
            if lat is None or lng is None:
                continue
            try:
                flat, flng = float(lat), float(lng)
            except (TypeError, ValueError):
                continue
            name = str(m.get("name") or f"장소 {i}")
            base = {}
            cid = m.get("content_id")
            if cid is not None and str(cid) in by_id:
                base = by_id[str(cid)]
            elif name in by_name:
                base = by_name[name]
            points.append(
                {
                    "order": int(m.get("order") or i),
                    "name": name,
                    "lat": flat,
                    "lng": flng,
                    "category": str(
                        m.get("category") or base.get("category") or ""
                    ),
                    "address": str(m.get("address") or base.get("address") or ""),
                    "reason": str(m.get("reason") or base.get("reason") or ""),
                    "duration": str(m.get("duration") or base.get("duration") or ""),
                    "travel_time": str(
                        m.get("travel_time") or base.get("travel_time") or ""
                    ),
                    "image": str(m.get("image") or base.get("image") or ""),
                    "content_id": str(
                        m.get("content_id") or base.get("content_id") or ""
                    ),
                }
            )
        return points

    # markers 없을 때 places 에서 직접
    if places:
        for i, p in enumerate(places, start=1):
            lat, lng = p.get("latitude"), p.get("longitude")
            if lat is None or lng is None:
                continue
            try:
                flat, flng = float(lat), float(lng)
            except (TypeError, ValueError):
                continue
            points.append(
                {
                    "order": i,
                    "name": str(p.get("name") or f"장소 {i}"),
                    "lat": flat,
                    "lng": flng,
                    "category": str(p.get("category") or ""),
                    "address": str(p.get("address") or ""),
                    "reason": str(p.get("reason") or ""),
                    "duration": str(p.get("duration") or ""),
                    "travel_time": str(p.get("travel_time") or ""),
                    "image": str(p.get("image") or ""),
                    "content_id": str(p.get("content_id") or ""),
                }
            )
    return points


def _render_text_route(places: list[dict[str, Any]]) -> None:
    for i, p in enumerate(places, start=1):
        st.markdown(
            f"**{i}. {p.get('name', '장소')}** · {p.get('category', '-')}  \n"
            f"{p.get('address') or ''}  \n"
            f"{p.get('reason') or ''}"
        )


def _leaflet_route_html(points: list[dict[str, Any]]) -> str:
    """Leaflet: 빨간 숫자 마커 + 화살표 폴리라인 + 팝업 + 좌하단 루트 패널."""
    pts_json = json.dumps(points, ensure_ascii=False)
    # escape for script embedding
    pts_json = pts_json.replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.js"></script>
  <style>
    html, body {{ margin:0; padding:0; height:100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
    #map {{ width:100%; height:540px; border-radius:12px; }}
    .num-marker {{
      background:#e53935;
      color:#fff;
      border:2px solid #fff;
      border-radius:50%;
      width:28px; height:28px;
      display:flex; align-items:center; justify-content:center;
      font:700 13px/1 sans-serif;
      box-shadow:0 2px 6px rgba(0,0,0,.35);
    }}
    .popup-card {{ min-width:200px; max-width:260px; }}
    .popup-card h4 {{ margin:0 0 6px; font-size:14px; color:#1a1a1a; }}
    .popup-card .meta {{ color:#555; font-size:12px; margin:2px 0; }}
    .popup-card .reason {{ margin-top:8px; font-size:12.5px; line-height:1.45; color:#222; }}
    .popup-card img {{ width:100%; max-height:120px; object-fit:cover; border-radius:8px; margin-bottom:8px; }}
    .route-panel {{
      position:absolute; left:12px; bottom:12px; z-index:1000;
      background:rgba(255,255,255,.96);
      border-radius:12px;
      box-shadow:0 4px 16px rgba(0,0,0,.18);
      padding:10px 12px;
      max-width:min(280px, 70vw);
      max-height:220px;
      overflow:auto;
      border:1px solid #e8eaed;
    }}
    .route-panel h5 {{
      margin:0 0 8px; font-size:12px; letter-spacing:.02em;
      color:#333; text-transform:uppercase;
    }}
    .route-panel ol {{ margin:0; padding-left:18px; }}
    .route-panel li {{
      font-size:12.5px; margin:4px 0; color:#222; cursor:pointer;
      line-height:1.35;
    }}
    .route-panel li:hover {{ color:#e53935; }}
    .route-panel .cat {{ color:#777; font-size:11px; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="route-panel" id="routePanel">
    <h5>Route order</h5>
    <ol id="routeList"></ol>
  </div>
  <script>
    (function() {{
      var points = {pts_json};
      if (!points || !points.length) return;

      var map = L.map('map', {{ zoomControl: true }});
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
      }}).addTo(map);

      var latlngs = [];
      var markers = [];

      function popupHtml(p) {{
        var img = p.image
          ? '<img src="' + p.image.replace(/"/g,'&quot;') + '" alt=""/>'
          : '';
        var reason = p.reason
          ? '<div class="reason">' + escapeHtml(p.reason) + '</div>'
          : '';
        return '<div class="popup-card">'
          + img
          + '<h4>' + p.order + '. ' + escapeHtml(p.name || '') + '</h4>'
          + '<div class="meta">' + escapeHtml(p.category || '-') + '</div>'
          + '<div class="meta">' + escapeHtml(p.address || '') + '</div>'
          + (p.duration ? '<div class="meta">체류: ' + escapeHtml(p.duration) + '</div>' : '')
          + (p.travel_time ? '<div class="meta">이동: ' + escapeHtml(p.travel_time) + '</div>' : '')
          + reason
          + '</div>';
      }}

      function escapeHtml(s) {{
        return String(s)
          .replace(/&/g,'&amp;').replace(/</g,'&lt;')
          .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
      }}

      function numIcon(n) {{
        return L.divIcon({{
          className: '',
          html: '<div class="num-marker">' + n + '</div>',
          iconSize: [28, 28],
          iconAnchor: [14, 14],
          popupAnchor: [0, -16]
        }});
      }}

      var list = document.getElementById('routeList');
      points.forEach(function(p, idx) {{
        var ll = L.latLng(p.lat, p.lng);
        latlngs.push(ll);
        var m = L.marker(ll, {{ icon: numIcon(p.order || (idx+1)) }})
          .addTo(map)
          .bindPopup(popupHtml(p), {{ maxWidth: 280 }});
        markers.push(m);

        var li = document.createElement('li');
        li.innerHTML = '<b>' + escapeHtml(p.name || '') + '</b>'
          + (p.category ? ' <span class="cat">' + escapeHtml(p.category) + '</span>' : '');
        li.onclick = function() {{
          map.setView(ll, Math.max(map.getZoom(), 15));
          m.openPopup();
        }};
        list.appendChild(li);
      }});

      // 빨간 연결선
      var line = L.polyline(latlngs, {{
        color: '#e53935',
        weight: 4,
        opacity: 0.9,
        lineJoin: 'round'
      }}).addTo(map);

      // 화살표 (다음 지점 방향)
      if (typeof L.polylineDecorator === 'function') {{
        L.polylineDecorator(line, {{
          patterns: [
            {{
              offset: 25,
              repeat: 50,
              symbol: L.Symbol.arrowHead({{
                pixelSize: 12,
                polygon: false,
                pathOptions: {{
                  stroke: true,
                  color: '#c62828',
                  weight: 3
                }}
              }})
            }}
          ]
        }}).addTo(map);
      }} else {{
        // decorator 로드 실패 시 세그먼트 중간 작은 화살표 대체
        for (var i = 0; i < latlngs.length - 1; i++) {{
          var a = latlngs[i], b = latlngs[i+1];
          var mid = L.latLng((a.lat+b.lat)/2, (a.lng+b.lng)/2);
          var angle = Math.atan2(b.lng - a.lng, b.lat - a.lat) * 180 / Math.PI;
          L.marker(mid, {{
            icon: L.divIcon({{
              className: '',
              html: '<div style="transform:rotate(' + angle + 'deg);color:#c62828;font-size:16px;font-weight:700">▲</div>',
              iconSize: [16,16], iconAnchor: [8,8]
            }}),
            interactive: false
          }}).addTo(map);
        }}
      }}

      map.fitBounds(L.latLngBounds(latlngs).pad(0.18));
      // 첫 마커 팝업은 자동으로 열지 않음 (사용자 클릭)
    }})();
  </script>
</body>
</html>
"""


def _naver_place_url(name: str, lat: float, lon: float) -> str:
    q = quote(name or f"{lat},{lon}")
    return f"https://map.naver.com/v5/search/{q}?c={lon},{lat},16,0,0,0,dh"
