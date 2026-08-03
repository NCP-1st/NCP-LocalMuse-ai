#!/usr/bin/env bash
# LocalMuse AI — Streamlit 실행
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
exec streamlit run FE/app.py --server.headless true
