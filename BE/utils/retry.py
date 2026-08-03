"""간단한 재시도 헬퍼 (TourAPI 등 외부 호출용)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_retry(
    fn: Callable[[], T],
    *,
    retries: int = 2,
    delay_sec: float = 0.6,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    label: str = "operation",
) -> T:
    """
    fn 을 최대 retries+1 회 실행. 마지막 실패는 예외를 다시 던진다.
    """
    last: BaseException | None = None
    attempts = max(0, retries) + 1
    for i in range(attempts):
        try:
            return fn()
        except exceptions as exc:  # noqa: PERF203
            last = exc
            if i >= attempts - 1:
                break
            logger.warning(
                "%s 실패 (%d/%d): %s — %.1fs 후 재시도",
                label,
                i + 1,
                attempts,
                exc,
                delay_sec,
            )
            time.sleep(delay_sec)
    assert last is not None
    raise last
