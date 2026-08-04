"""
LocalMuse AI — 선형(SVG stroke) 아이콘.

규칙 (프로젝트 전역, 앞으로도 동일):
- 이모지(emoji) 사용 금지
- UI 장식/상태 표시는 이 모듈의 선형 SVG 만 사용
- stroke 기반, fill 없음, currentColor 상속

사용 예:
    st.markdown(f"{icon('compass')} LocalMuse AI", unsafe_allow_html=True)
    st.markdown(icon_text('map-pin', address), unsafe_allow_html=True)
"""

from __future__ import annotations

from html import escape

# name -> path d (viewBox 0 0 24 24, lucide-style linear)
_PATHS: dict[str, str] = {
    # brand / nav
    "compass": (
        "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z "
        "M16.2 7.8l-2.4 5.4-5.4 2.4 2.4-5.4 5.4-2.4z"
    ),
    "map": (
        "M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6z "
        "M9 3v15 M15 6v15"
    ),
    "map-pin": (
        "M12 21s-6-5.3-6-10a6 6 0 1 1 12 0c0 4.7-6 10-6 10z "
        "M12 11a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"
    ),
    # status
    "check": "M5 12l4 4L19 6",
    "check-circle": (
        "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M8 12l3 3 5-6"
    ),
    "x": "M6 6l12 12 M18 6L6 18",
    "x-circle": (
        "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M15 9l-6 6 M9 9l6 6"
    ),
    "alert": (
        "M12 3L2 20h20L12 3z M12 10v4 M12 17h.01"
    ),
    "circle": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z",
    "dot": "M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0",
    # actions / demo
    "zap": "M13 2L4 14h7l-1 8 9-12h-7l1-8z",
    "play": "M7 5v14l12-7L7 5z",
    "save": (
        "M5 3h11l3 3v15H5V3z M8 3v6h8 M8 21v-7h8v7"
    ),
    "refresh": (
        "M3 12a9 9 0 0 1 15-6.7L21 8 M21 3v5h-5 "
        "M21 12a9 9 0 0 1-15 6.7L3 16 M3 21v-5h5"
    ),
    # context
    "clock": (
        "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 6v6l4 2"
    ),
    "walk": (
        "M13 4a2 2 0 1 0 0-4 2 2 0 0 0 0 4z "
        "M8 21l3-7 2 2 3 5 M14 14l-1.5-3 3-2 3 4"
    ),
    "message": (
        "M4 5h16v11H8l-4 4V5z"
    ),
    "activity": (
        "M3 12h4l2-7 4 14 2-7h6"
    ),
    "database": (
        "M4 6c0 1.7 3.6 3 8 3s8-1.3 8-3-3.6-3-8-3-8 1.3-8 3z "
        "M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6 "
        "M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"
    ),
    "route": (
        "M4 18h4a4 4 0 0 0 0-8H8a4 4 0 0 1 0-8h4 "
        "M16 6h4 M16 18h4 M18 4v4 M18 16v4"
    ),
    "chevron-right": "M9 6l6 6-6 6",
    "list": "M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01",
    "spark": (
        "M12 2v4 M12 18v4 M4.9 4.9l2.8 2.8 M16.3 16.3l2.8 2.8 "
        "M2 12h4 M18 12h4 M4.9 19.1l2.8-2.8 M16.3 7.7l2.8-2.8"
    ),
}


def icon(
    name: str,
    *,
    size: int = 18,
    class_name: str = "lm-icon",
    stroke_width: float = 1.75,
    title: str | None = None,
) -> str:
    """인라인 선형 SVG 마크업 반환."""
    d = _PATHS.get(name)
    if not d:
        d = _PATHS["circle"]
        name = "circle"

    title_html = f"<title>{escape(title or name)}</title>" if title else ""
    return (
        f'<svg class="{escape(class_name)}" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" '
        f'aria-hidden="true" focusable="false">'
        f"{title_html}"
        f'<path d="{d}" stroke="currentColor" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f"</svg>"
    )


def icon_text(
    name: str,
    text: str,
    *,
    size: int = 16,
    gap: str = "0.35rem",
) -> str:
    """아이콘 + 텍스트 한 줄."""
    return (
        f'<span class="lm-icon-row" style="gap:{gap}">'
        f"{icon(name, size=size)}"
        f"<span>{escape(str(text))}</span>"
        f"</span>"
    )


def icon_heading(name: str, text: str, *, level: int = 3, size: int = 22) -> str:
    """제목용 아이콘+텍스트 (h1~h6 스타일 클래스)."""
    level = max(1, min(6, level))
    return (
        f'<div class="lm-icon-heading lm-h{level}">'
        f"{icon(name, size=size)}"
        f"<span>{escape(str(text))}</span>"
        f"</div>"
    )


def status_icon(ok: bool, *, size: int = 14) -> str:
    """설정/상태 OK vs empty."""
    if ok:
        return icon("check-circle", size=size, class_name="lm-icon lm-icon-ok")
    return icon("circle", size=size, class_name="lm-icon lm-icon-muted")


def warn_icon(*, size: int = 14) -> str:
    return icon("alert", size=size, class_name="lm-icon lm-icon-warn")


def error_icon(*, size: int = 14) -> str:
    return icon("x-circle", size=size, class_name="lm-icon lm-icon-err")


def ok_icon(*, size: int = 14) -> str:
    return icon("check-circle", size=size, class_name="lm-icon lm-icon-ok")
