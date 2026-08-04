"""성수 E2E — 키 없어도 stub 경로로 demo_ok 가능해야 함."""

from BE.services.e2e import run_seongsu_e2e


def test_seongsu_e2e_stub_demo_ok():
    report = run_seongsu_e2e(save=False, probe=False)
    assert "verdict" in report
    assert "course" in report
    assert report["scenario"]["location"] == "성수"
    # stub 환경에서도 코스 3곳 이상
    assert report["verdict"]["demo_ok"] is True
    assert report["course"]["place_count"] >= 3
