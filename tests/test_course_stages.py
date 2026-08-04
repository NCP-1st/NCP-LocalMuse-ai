from BE.services.course import generate_course


def test_generate_course_emits_stages():
    seen: list[str] = []

    def on_stage(name: str, payload: dict) -> None:
        seen.append(name)

    result = generate_course(
        location="성수",
        purpose="감성 카페와 산책",
        time="3시간",
        transport="도보",
        save=False,
        on_stage=on_stage,
    )
    assert "tourapi" in seen
    assert "clova" in seen
    assert "maps" in seen
    assert "done" in seen
    assert result.get("stages")
    assert result.get("elapsed_ms") is not None
    assert len(result.get("places") or []) >= 3
