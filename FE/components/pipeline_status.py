"""코스 생성 단계 로딩 UI — 선형 SVG 아이콘 (이모지 금지)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from BE.services.course import generate_course
from FE.components.icons import error_icon, icon, ok_icon, warn_icon

STAGE_META: dict[str, dict[str, Any]] = {
    "tourapi": {
        "label": "1 TourAPI",
        "detail": "관광 장소 후보 수집",
        "pct": 20,
        "icon": "list",
    },
    "clova": {
        "label": "2 CLOVA Studio",
        "detail": "코스 · 추천 이유 · 지역 스토리 생성",
        "pct": 55,
        "icon": "spark",
    },
    "maps": {
        "label": "3 Maps",
        "detail": "좌표 보강 · 이동 동선 구성",
        "pct": 80,
        "icon": "map",
    },
    "save": {
        "label": "4 저장",
        "detail": "코스 · 히스토리 DB 기록",
        "pct": 92,
        "icon": "save",
    },
    "done": {
        "label": "완료",
        "detail": "추천 결과 준비됨",
        "pct": 100,
        "icon": "check-circle",
    },
}


def run_course_with_stage_ui(
    *,
    location: str,
    purpose: str,
    time: str,
    transport: str,
    user_id: int | None,
    save: bool = True,
) -> dict[str, Any]:
    """generate_course 호출 + progress / status 단계 표시."""
    progress = st.progress(0, text="준비 중…")
    log_box = st.empty()
    lines: list[str] = []

    with st.status("여행 코스 생성 중… (목표 10초 이내)", expanded=True) as status:

        def on_stage(name: str, payload: dict[str, Any]) -> None:
            meta = STAGE_META.get(
                name, {"label": name, "detail": "", "pct": 50, "icon": "circle"}
            )
            msg = payload.get("message") or payload.get("status") or ""
            ic = icon(str(meta.get("icon") or "circle"), size=14)
            st_label = f"{ic} <b>{meta['label']}</b> — {meta['detail']}"
            if msg:
                st_label = f"{st_label} · {msg}"

            pct = int(meta.get("pct") or 50)
            st_code = payload.get("status")
            if st_code == "error":
                lines.append(f"{error_icon(size=14)} {st_label}")
            elif st_code == "partial":
                lines.append(f"{warn_icon(size=14)} {st_label}")
            else:
                lines.append(f"{ic} {st_label}")

            progress.progress(min(pct, 100), text=str(meta["label"]))
            log_box.markdown(
                "<br/>".join(f'<div class="lm-icon-row">{x}</div>' for x in lines),
                unsafe_allow_html=True,
            )
            status.update(label=f"진행 중: {meta['label']}", state="running")

        result = generate_course(
            location=location,
            purpose=purpose,
            time=time,
            transport=transport,
            user_id=user_id,
            save=save,
            on_stage=on_stage,
        )

        elapsed = result.get("elapsed_ms")
        if result.get("places"):
            progress.progress(100, text="완료")
            status.update(
                label=f"완료 · {elapsed}ms" if elapsed else "완료",
                state="complete",
            )
        else:
            status.update(
                label=result.get("message") or "실패",
                state="error",
            )
            progress.progress(100, text="실패")

    return result


def render_stage_timeline(result: dict[str, Any]) -> None:
    """완료 후 단계 타임라인 요약."""
    stages = result.get("stages") or []
    if not stages:
        return

    with st.expander("파이프라인 단계 로그", expanded=False):
        rows = []
        for s in stages:
            if not isinstance(s, dict):
                continue
            name = s.get("stage", "")
            meta = STAGE_META.get(name, {})
            rows.append(
                {
                    "단계": meta.get("label") or name,
                    "상태": s.get("status", ""),
                    "메시지": s.get("message", ""),
                }
            )
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)
        elapsed = result.get("elapsed_ms")
        if elapsed is not None:
            target = 10_000
            ok = elapsed <= target
            mark = ok_icon(size=14) if ok else warn_icon(size=14)
            label = "달성" if ok else "초과"
            st.markdown(
                f'{mark} 소요 {elapsed} ms · NFR 목표 10초 이내 — {label}',
                unsafe_allow_html=True,
            )
