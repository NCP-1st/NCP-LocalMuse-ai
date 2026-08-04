"""
DB 연결.

우선순위:
  1) DATABASE_URL
  2) DB_HOST + DB_USER + DB_NAME → MySQL (NCP Cloud DB)
     - 접속 실패 시 DB_FALLBACK_SQLITE=true 이면 SQLite 폴백 (로컬 개발)
  3) SQLite 로컬 파일

보안 (PRD): 접속 정보는 환경변수만 사용.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_mysql_unreachable: bool | None = None  # 프로세스 내 캐시


def _fallback_sqlite_enabled() -> bool:
    raw = os.getenv("DB_FALLBACK_SQLITE", "true").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def get_connection_info() -> dict[str, Any]:
    s = get_settings()
    kind = _resolve_kind(s)
    return {
        "kind": kind,
        "host": s.db_host,
        "port": s.db_port,
        "database": s.db_name,
        "user": s.db_user,
        "sqlite_path": s.sqlite_path,
        "mysql_configured": bool(s.db_host and s.db_user and s.db_name),
        "fallback_sqlite": _fallback_sqlite_enabled(),
        "configured": True,
    }


def _resolve_kind(s: Any) -> str:
    global _mysql_unreachable
    if s.db_url:
        return "url"
    if s.db_host and s.db_user and s.db_name:
        if _mysql_unreachable and _fallback_sqlite_enabled():
            return "sqlite"
        return "mysql"
    return "sqlite"


def ping() -> bool:
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        logger.exception("DB ping 실패")
        return False


def reset_mysql_probe() -> None:
    """테스트용: MySQL 도달 불가 캐시 초기화."""
    global _mysql_unreachable
    _mysql_unreachable = None


@contextmanager
def connect() -> Generator[Any, None, None]:
    """DB-API 커넥션 컨텍스트."""
    global _mysql_unreachable
    s = get_settings()
    kind = _resolve_kind(s)

    if kind == "mysql":
        try:
            conn = _connect_mysql(s)
            _mysql_unreachable = False
        except Exception as exc:
            if _fallback_sqlite_enabled():
                logger.warning(
                    "MySQL 접속 실패 → SQLite 폴백 (%s: %s)",
                    type(exc).__name__,
                    str(exc)[:120],
                )
                _mysql_unreachable = True
                conn = _connect_sqlite(s.sqlite_path)
            else:
                raise
    else:
        conn = _connect_sqlite(s.sqlite_path)

    try:
        _ensure_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _connect_sqlite(path: str) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _connect_mysql(s: Any) -> Any:
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "MySQL 사용 시 pymysql 이 필요합니다: pip install pymysql"
        ) from exc

    # connect_timeout 짧게 — VPC 밖 타임아웃 대기 줄임
    conn = pymysql.connect(
        host=s.db_host,
        port=s.db_port,
        user=s.db_user,
        password=s.db_password,
        database=s.db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
        read_timeout=15,
        write_timeout=15,
    )
    return conn


def _ensure_schema(conn: Any) -> None:
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    cur = conn.cursor()
    is_mysql = not isinstance(conn, sqlite3.Connection)

    for stmt in statements:
        adapted = stmt
        if is_mysql:
            adapted = (
                stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "INT PRIMARY KEY AUTO_INCREMENT")
                .replace("DOUBLE", "DOUBLE")
            )
        try:
            cur.execute(adapted)
        except Exception as exc:
            msg = str(exc).lower()
            if "already exists" in msg or "duplicate" in msg:
                continue
            if "auto_increment" in msg:
                continue
            logger.debug("schema stmt skip/warn: %s (%s)", exc, adapted[:60])
