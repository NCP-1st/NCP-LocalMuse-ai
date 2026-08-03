"""Streamlit 실행 시 레포 루트를 sys.path 에 추가해 BE import 가능하게 함."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def ensure_repo_root_on_path() -> Path:
    root = str(_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return _ROOT


def repo_root() -> Path:
    return _ROOT
