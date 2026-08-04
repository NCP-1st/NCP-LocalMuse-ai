#!/usr/bin/env bash
# PRD 성수 시나리오 E2E (키 값은 출력하지 않음)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

echo "== health --probe =="
python -m BE health --probe
echo
echo "== e2e (성수 PRD) =="
python -m BE e2e
