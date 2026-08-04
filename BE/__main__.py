"""CLI: python -m BE [health|course|e2e]"""

from __future__ import annotations

import json
import sys

from BE.services.course import generate_course
from BE.services.e2e import run_seongsu_e2e
from BE.services.health import get_health
from BE.utils.config import clear_settings_cache
from BE.utils.logging_setup import setup_logging


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    clear_settings_cache()
    args = list(argv if argv is not None else sys.argv[1:])
    probe = False
    if "--probe" in args:
        probe = True
        args = [a for a in args if a != "--probe"]

    cmd = args[0] if args else "health"

    if cmd == "health":
        print(json.dumps(get_health(probe=probe), ensure_ascii=False, indent=2))
        return 0

    if cmd == "e2e":
        # 성수 PRD 시나리오 — 기본 probe 포함
        do_probe = probe or True
        report = run_seongsu_e2e(save=False, probe=do_probe)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        verdict = report.get("verdict") or {}
        # exit code: 0 demo ok, 1 fail
        if verdict.get("live_demo_ok") or verdict.get("demo_ok"):
            return 0
        return 1

    if cmd == "course":
        location = args[1] if len(args) > 1 else "성수"
        purpose = args[2] if len(args) > 2 else "감성 카페와 산책"

        def on_stage(name: str, payload: dict) -> None:
            print(f"[stage] {name}: {payload}", file=sys.stderr)

        result = generate_course(
            location=location,
            purpose=purpose,
            time="3시간",
            transport="도보",
            save=False,
            on_stage=on_stage,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0

    print(
        "Usage:\n"
        "  python -m BE health [--probe]\n"
        "  python -m BE e2e          # 성수 PRD E2E + probe\n"
        "  python -m BE course [location] [purpose]\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
