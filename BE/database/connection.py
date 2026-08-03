"""
DB 연결.

우선순위:
  1) DATABASE_URL (SQLAlchemy URL)
  2) DB_HOST/USER/NAME → MySQL (NCP Cloud DB)
  3) SQLite 로컬 파일 (개발용, data/localmuse.sqlite3)

보안 (PRD): 접속 정보는 환경변수만 사용.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterator

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection_info() -> dict[str, Any]:
    s = get_settings()
    if s.db_url:
        kind = "url"
    elif s.db_host and s.db_user and s.db_name:
        kind = "mysql"
    else:
        kind = "sqlite"
    return {
        "kind": kind,
        "host": s.db_host,
        "port": s.db_port,
        "database": s.db_name,
        "user": s.db_user,
        "sqlite_path": s.sqlite_path,
        "configured": True,
    }


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


@contextmanager
def connect() -> Generator[Any, None, None]:
    """DB-API 커넥션 컨텍스트."""
    s = get_settings()
    info = get_connection_info()

    if info["kind"] == "mysql":
        conn = _connect_mysql(s)
    else:
        conn = _connect_sqlite(s.sqlite_path)

    try:
        _ensure_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
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

    conn = pymysql.connect(
        host=s.db_host,
        port=s.db_port,
        user=s.db_user,
        password=s.db_password,
        database=s.db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return conn


def _ensure_schema(conn: Any) -> None:
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    # SQLite executescript / MySQL multi statement 단순 분리
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    cur = conn.cursor()
    for stmt in statements:
        # MySQL 은 AUTOINCREMENT → AUTO_INCREMENT 가 이상적이나,
        # SQLite 스키마로 로컬 우선. MySQL 은 별도 마이그레이션 권장.
        try:
            cur.execute(stmt)
        except Exception as exc:
            # 이미 존재하는 테이블 등 무시 가능한 경우
            msg = str(exc).lower()
            if "already exists" in msg or "duplicate" in msg:
                continue
            # SQLite 에서 INTEGER PRIMARY KEY AUTOINCREMENT 는 정상
            if "auto_increment" in msg:
                continue
            logger.debug("schema stmt skip/warn: %s (%s)", exc, stmt[:60])
