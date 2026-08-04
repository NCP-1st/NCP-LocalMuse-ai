"""저장된 코스 조회 (DB History / Course). 선형 SVG 아이콘."""

from __future__ import annotations

import streamlit as st

from FE.lib.bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from BE.database.connection import connect  # noqa: E402
from BE.database.repository import get_course  # noqa: E402
from FE.components.icons import icon_heading  # noqa: E402
from FE.components.styles import inject_styles  # noqa: E402

st.set_page_config(
    page_title="저장 코스 · LocalMuse",
    page_icon=None,
    layout="wide",
)
inject_styles()

st.markdown(icon_heading("save", "저장 코스", level=1, size=26), unsafe_allow_html=True)
st.caption("로컬 SQLite / NCP Cloud DB에 저장된 추천 결과")

course_id = st.number_input("Course ID", min_value=1, step=1, value=1)
cols = st.columns(2)
load = cols[0].button("코스 불러오기", type="primary")
list_recent = cols[1].button("최근 기록 보기")

if list_recent:
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, title, source, created_at
                FROM courses
                ORDER BY id DESC
                LIMIT 20
                """
            )
            rows = cur.fetchall()
        if not rows:
            st.info("저장된 코스가 없습니다. 홈에서 먼저 추천을 받아 보세요.")
        else:
            data = []
            for r in rows:
                if hasattr(r, "keys"):
                    data.append({k: r[k] for k in r.keys()})
                else:
                    data.append(
                        {
                            "id": r[0],
                            "title": r[1],
                            "source": r[2],
                            "created_at": r[3],
                        }
                    )
            st.dataframe(data, use_container_width=True)
    except Exception as exc:
        st.error(f"목록 조회 실패: {exc}")

if load:
    try:
        detail = get_course(int(course_id))
        if not detail:
            st.warning("해당 ID의 코스가 없습니다.")
        else:
            course = detail["course"]
            st.subheader(course.get("title") or f"Course #{course_id}")
            if course.get("story"):
                st.write(course["story"])
            st.caption(
                f"source={course.get('source')} · created={course.get('created_at')}"
            )
            st.markdown("#### 장소")
            for p in detail["places"]:
                seq = p.get("sequence", "")
                st.markdown(
                    f"**{seq}. {p.get('name')}** · {p.get('category')}  \n"
                    f"{p.get('address')}  \n"
                    f"{p.get('reason') or ''}"
                )
    except Exception as exc:
        st.error(f"조회 실패: {exc}")
