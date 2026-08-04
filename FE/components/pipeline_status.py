"""코스 생성 단계 로딩 UI (Sprint A4)."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from BE.services.course import generate_course

STAGE_ORDER = ["tourapi", "clova", "maps", "save", "done"]

STAGE_META: dict[str, dict[str, str]] = {
    "tourapi": {
        "label": "① TourAPI",
        "detail": "관광 장소 후보 수집",
        "pct": 20,
    },
    "clova": {
        "label": "② CLOVA Studio",
        "detail": "코스 · 추천 이유 · 지역 스토리 생성",
        "pct": 55,
    },
    "maps": {
        "label": "③ Maps",
        "detail": "좌표 보강 · 이동 동선 구성",
        "pct": 80,
    },
    "save": {
        "label": "④ 저장",
        "detail": "코스 · 히스토리 DB 기록",
        "pct": 92,
    },
    "done": {
        "label": "✅ 완료",
        "detail": "추천 결과 준비됨",
        "pct": 100,
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
    """
    generate_course 를 호출하며 st.status + progress bar 로 단계를 표시한다.
    """
    progress = st.progress(0, text="준비 중…")
    log_box = st.empty()
    lines: list[str] = []

    with st.status("여행 코스 생성 중… (목표 10초 이내)", expanded=True) as status:

        def on_stage(name: str, payload: dict[str, Any]) -> None:
            meta = STAGE_META.get(name, {"label": name, "detail": "", "pct": 50})
            msg = payload.get("message") or payload.get("status") or ""
            st_label = f"{meta['label']} — {meta['detail']}"
            if msg:
                st_label = f"{st_label} · {msg}"

            pct = int(meta.get("pct") or 50)
            # error 시 진행률은 유지
            if payload.get("status") == "error":
                lines.append(f"❌ {st_label}")
            elif payload.get("status") == "partial":
                lines.append(f"⚠️ {st_label}")
            else:
                lines.append(f"▸ {st_label}")

            progress.progress(min(pct, 100), text=meta["label"])
            log_box.markdown("\n\n".join(f"- {x}" for x in lines))
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
            st.caption(
                f"소요 {elapsed} ms · NFR 목표 10초 이내 — "
                + ("달성 ✅" if ok else "초과 ⚠️")
            )
