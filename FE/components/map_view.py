"""
지도 영역 — Streamlit 안정 표시 + 네이버 지도 연동.

중요:
  Streamlit components.html 은 iframe(srcdoc) 안에서 maps.js 를 로드한다.
  NCP Dynamic Map 은 등록된 Web URL 과 실제 문서 origin 을 검사하므로
  iframe 임베드에서 'Open API 인증 실패' 가 자주 발생한다.
  (Client ID / localhost 등록이 맞아도 실패할 수 있음)

전략:
  1) 앱 안 지도: st.map (TourAPI 좌표) — 항상 동작
  2) 네이버 지도: 좌표/장소명 딥링크 (API 키·인증 불필요)
  3) Dynamic Map iframe: 선택(실험) — 실패 시 안내만
"""

from __future__ import annotations

import json
from html import escape
from typing import Any
from urllib.parse import quote

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
        "좌표: TourAPI · 앱 내 지도: Streamlit map · "
        "네이버 지도: 딥링크 (Geocode 미사용)"
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

    if not rows:
        st.info("마커 좌표가 없습니다. 텍스트 동선만 확인하세요.")
        return

    # —— 1) 앱 안 안정 지도 (인증 불필요) ——
    st.markdown(
        f'{icon("check-circle", size=14, class_name="lm-icon lm-icon-ok")} '
        f"<span>앱 내 지도 · 마커 {len(rows)}개 (TourAPI 좌표)</span>",
        unsafe_allow_html=True,
    )
    df = pd.DataFrame(rows)
    st.map(df[["lat", "lon"]], size=60, zoom=13)

    # —— 2) 네이버 지도 딥링크 (인증 불필요, 실제 네이버 지도 앱/웹) ——
    st.markdown("#### 네이버 지도에서 보기")
    st.caption(
        "Streamlit iframe 인증 문제를 피하기 위해, "
        "네이버 지도 웹/앱으로 바로 엽니다. (Client ID 불필요)"
    )

    # 전체 동선: 첫 지점 중심
    first = rows[0]
    overview_url = _naver_coord_url(first["lat"], first["lon"], zoom=15)
    st.link_button(
        "네이버 지도에서 코스 시작 지점 열기",
        overview_url,
        use_container_width=True,
        type="primary",
    )

    for r in rows:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                f"**{r['order']}. {r['name']}**  \n"
                f"{r.get('category') or '-'} · {r.get('address') or '-'}  \n"
                f"`{r['lat']:.5f}, {r['lon']:.5f}`"
            )
        with c2:
            place_url = _naver_place_url(r["name"], r["lat"], r["lon"])
            st.link_button("네이버 지도", place_url, use_container_width=True)

    # —— 3) Dynamic Map 실험 (실패 가능 — Streamlit iframe) ——
    client_id = (naver_client_id or route.get("naver_client_id") or "").strip()
    with st.expander(
        "실험: 앱 안 NAVER Dynamic Map (iframe · 인증 실패 가능)",
        expanded=False,
    ):
        st.warning(
            "Streamlit 은 지도를 **iframe** 안에 넣습니다. "
            "NCP Web URL 에 localhost 를 등록해도 iframe 문서는 별도 origin 이라 "
            "인증 실패가 날 수 있습니다. 키/등록이 맞아도 실패할 수 있는 구조 한계입니다."
        )
        st.markdown(
            """
**등록 확인 (Client ID 가 맞아도 필요)**  
Web 서비스 URL (최대 10개) — 아래 **4개 모두** 시도:

| 등록 URL |
|----------|
| `http://localhost` |
| `http://127.0.0.1` |
| `http://localhost:8501` |
| `http://127.0.0.1:8501` |

공식 문서는 포트 없이라고 하지만, 환경에 따라 **포트 포함**이 필요한 경우가 있습니다.
"""
        )
        if client_id:
            _render_naver_maps_iframe(rows, client_id=client_id)
        else:
            st.info("NAVER_MAP_CLIENT_ID 가 없어 Dynamic Map 실험을 건너뜁니다.")

    with st.expander("장소 좌표 목록", expanded=False):
        st.dataframe(
            pd.DataFrame(rows)[["order", "name", "category", "address", "lat", "lon"]],
            hide_index=True,
            use_container_width=True,
        )


def _naver_coord_url(lat: float, lon: float, zoom: int = 15) -> str:
    """네이버 지도 좌표 중심 URL (API 키 불필요)."""
    # map.naver.com v5 style center
    return f"https://map.naver.com/v5/?c={lon},{lat},{zoom},0,0,0,dh"


def _naver_place_url(name: str, lat: float, lon: float) -> str:
    """장소명 검색 + 좌표 힌트."""
    q = quote(name or f"{lat},{lon}")
    # 검색 결과 페이지
    return f"https://map.naver.com/v5/search/{q}?c={lon},{lat},16,0,0,0,dh"


def _render_naver_maps_iframe(
    rows: list[dict[str, Any]],
    *,
    client_id: str,
) -> None:
    """Dynamic Map iframe (Streamlit 구조상 인증 실패 가능)."""
    center_lat = sum(r["lat"] for r in rows) / len(rows)
    center_lng = sum(r["lon"] for r in rows) / len(rows)
    points_json = json.dumps(
        [
            {
                "lat": r["lat"],
                "lng": r["lon"],
                "name": r["name"],
                "order": r["order"],
            }
            for r in rows
        ],
        ensure_ascii=False,
    )
    cid = escape(client_id)

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    html,body{{margin:0;padding:0;height:100%;font-family:sans-serif}}
    #nmap{{width:100%;height:420px;border-radius:12px}}
    .nm-label{{background:#2F6FED;color:#fff;border-radius:999px;width:26px;height:26px;
      display:flex;align-items:center;justify-content:center;font:700 12px/1 sans-serif;
      border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.28)}}
    .nm-err{{padding:14px;background:#fdecec;color:#5c1a1a;border-radius:12px;font-size:13px;line-height:1.5}}
    code{{background:#fff;padding:1px 4px;border-radius:4px}}
  </style>
</head>
<body>
  <div id="nmap"></div>
  <script>
    window.navermap_authFailure = function() {{
      document.getElementById('nmap').innerHTML =
        '<div class="nm-err"><b>Dynamic Map 인증 실패 (예상 가능)</b><br/>'
        + 'Streamlit iframe 구조 한계일 수 있습니다.<br/>'
        + '위쪽 <b>앱 내 지도</b>와 <b>네이버 지도 딥링크</b>를 사용하세요.<br/>'
        + '등록 URL 재확인: <code>http://localhost</code> 및 '
        + '<code>http://localhost:8501</code></div>';
    }};
  </script>
  <script src="https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId={cid}"></script>
  <script>
    (function(){{
      if (typeof naver === 'undefined' || !naver.maps) {{
        if (!document.querySelector('.nm-err')) {{
          document.getElementById('nmap').innerHTML =
            '<div class="nm-err">Maps 로드 실패. 딥링크/앱 내 지도를 사용하세요.</div>';
        }}
        return;
      }}
      var points = {points_json};
      var map = new naver.maps.Map('nmap', {{
        center: new naver.maps.LatLng({center_lat}, {center_lng}),
        zoom: 14,
        zoomControl: true
      }});
      var bounds = new naver.maps.LatLngBounds();
      var path = [];
      points.forEach(function(p){{
        var ll = new naver.maps.LatLng(p.lat, p.lng);
        path.push(ll); bounds.extend(ll);
        new naver.maps.Marker({{
          position: ll, map: map, title: p.name,
          icon: {{ content: '<div class="nm-label">'+p.order+'</div>',
                   anchor: new naver.maps.Point(13,13) }}
        }});
      }});
      if (path.length > 1) {{
        new naver.maps.Polyline({{
          map: map, path: path, strokeColor: '#2F6FED',
          strokeWeight: 4, strokeOpacity: 0.88
        }});
      }}
      map.fitBounds(bounds, {{ top:40, right:40, bottom:40, left:40 }});
    }})();
  </script>
</body>
</html>
"""
    components.html(html, height=440, scrolling=False)
