"""Course / Location / History 영속화."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from BE.database.connection import connect

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sql(conn: Any, statement: str) -> str:
    """SQLite 는 `?`, MySQL(pymysql) 은 `%s`."""
    if isinstance(conn, sqlite3.Connection):
        return statement
    return statement.replace("?", "%s")


def _row_id(row: Any, key: str = "id") -> int:
    if isinstance(row, dict):
        return int(row[key])
    # sqlite3.Row
    return int(row[0] if key == "id" and key not in row.keys() else row[key])


def ensure_user(nickname: str = "guest") -> int:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            _sql(conn, "SELECT id FROM users WHERE nickname = ? LIMIT 1"),
            (nickname,),
        )
        row = cur.fetchone()
        if row:
            return _row_id(row)
        cur.execute(
            _sql(conn, "INSERT INTO users (nickname, created_at) VALUES (?, ?)"),
            (nickname, _now()),
        )
        return int(cur.lastrowid)


def upsert_location(place: dict[str, Any]) -> int:
    name = str(place.get("name") or "unknown")
    address = str(place.get("address") or "")
    lat = float(place.get("latitude") or 0.0)
    lng = float(place.get("longitude") or 0.0)
    category = str(place.get("category") or "")
    content_id = place.get("content_id")

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            _sql(
                conn,
                "SELECT id FROM locations WHERE name = ? AND address = ? LIMIT 1",
            ),
            (name, address),
        )
        row = cur.fetchone()
        if row:
            return _row_id(row)
        cur.execute(
            _sql(
                conn,
                """
                INSERT INTO locations (name, address, latitude, longitude, category, content_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
            ),
            (name, address, lat, lng, category, content_id),
        )
        return int(cur.lastrowid)


def save_course(
    *,
    title: str,
    story: str | None,
    places: list[dict[str, Any]],
    user_id: Optional[int] = None,
    source: str | None = None,
    query: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
) -> int:
    """
    Course + CourseLocation + History 저장.
    Returns: course_id
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            _sql(
                conn,
                """
                INSERT INTO courses (user_id, title, story, source, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
            ),
            (user_id, title, story, source, _now()),
        )
        course_id = int(cur.lastrowid)

        for seq, place in enumerate(places, start=1):
            name = str(place.get("name") or "unknown")
            address = str(place.get("address") or "")
            lat = float(place.get("latitude") or 0.0)
            lng = float(place.get("longitude") or 0.0)
            category = str(place.get("category") or "")
            content_id = place.get("content_id")

            cur.execute(
                _sql(
                    conn,
                    "SELECT id FROM locations WHERE name = ? AND address = ? LIMIT 1",
                ),
                (name, address),
            )
            row = cur.fetchone()
            if row:
                location_id = _row_id(row)
            else:
                cur.execute(
                    _sql(
                        conn,
                        """
                        INSERT INTO locations
                          (name, address, latitude, longitude, category, content_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                    ),
                    (name, address, lat, lng, category, content_id),
                )
                location_id = int(cur.lastrowid)

            cur.execute(
                _sql(
                    conn,
                    """
                    INSERT INTO course_locations
                      (course_id, location_id, sequence, duration, travel_time, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                ),
                (
                    course_id,
                    location_id,
                    seq,
                    place.get("duration"),
                    place.get("travel_time"),
                    place.get("reason"),
                ),
            )

        if query is not None or result is not None:
            cur.execute(
                _sql(
                    conn,
                    """
                    INSERT INTO history (user_id, query_json, result_json, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                ),
                (
                    user_id,
                    json.dumps(query or {}, ensure_ascii=False),
                    json.dumps(result or {}, ensure_ascii=False),
                    _now(),
                ),
            )

        logger.info("saved course_id=%s places=%d", course_id, len(places))
        return course_id


def get_course(course_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            _sql(conn, "SELECT * FROM courses WHERE id = ?"),
            (course_id,),
        )
        course = cur.fetchone()
        if not course:
            return None
        cur.execute(
            _sql(
                conn,
                """
                SELECT cl.sequence, cl.duration, cl.travel_time, cl.reason,
                       l.name, l.address, l.latitude, l.longitude, l.category, l.content_id
                FROM course_locations cl
                JOIN locations l ON l.id = cl.location_id
                WHERE cl.course_id = ?
                ORDER BY cl.sequence ASC
                """,
            ),
            (course_id,),
        )
        rows = cur.fetchall()

    def _as_dict(r: Any) -> dict[str, Any]:
        if isinstance(r, dict):
            return r
        return {k: r[k] for k in r.keys()}

    return {"course": _as_dict(course), "places": [_as_dict(r) for r in rows]}
