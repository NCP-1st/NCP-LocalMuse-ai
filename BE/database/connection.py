"""
NCP Cloud DB 연결 스텁.

보안 (PRD):
  - 외부 접근 차단
  - 접속 정보는 환경변수만 사용
"""

from __future__ import annotations

import logging
from typing import Any

from BE.utils.config import get_settings

logger = logging.getLogger(__name__)


def get_connection_info() -> dict[str, Any]:
    """연결 설정 요약 (비밀번호 제외). 실제 커넥션은 DB 종류 확정 후 구현."""
    s = get_settings()
    return {
        "host": s.db_host,
        "port": s.db_port,
        "database": s.db_name,
        "user": s.db_user,
        "configured": bool(s.db_host and s.db_user and s.db_name),
    }


def ping() -> bool:
    """DB 연결 가능 여부. 미구현 시 False."""
    info = get_connection_info()
    if not info["configured"]:
        logger.warning("DB 환경변수 미설정")
        return False
    # TODO: NCP Cloud DB 실연결
    return False
