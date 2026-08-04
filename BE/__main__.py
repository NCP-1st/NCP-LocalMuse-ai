"""CLI 스모크: python -m BE"""

from __future__ import annotations

import json
import sys

from BE.services.course import generate_course
from BE.services.health import get_health
from BE.utils.logging_setup import setup_logging


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = list(argv if argv is not None else sys.argv[1:])
    probe = False
    if "--probe" in args:
        probe = True
        args = [a for a in args if a != "--probe"]

    cmd = args[0] if args else "health"

    if cmd == "health":
        print(json.dumps(get_health(probe=probe), ensure_ascii=False, indent=2))
        return 0

    if cmd == "course":
        location = args[1] if len(args) > 1 else "성수"
        purpose = args[2] if len(args) > 2 else "감성 카페와 산책"
        stages: list[str] = []

        def on_stage(name: str, payload: dict) -> None:
            stages.append(name)
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

    print("Usage: python -m BE [health|course] [--probe] [location] [purpose]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
