from BE.services.health import get_health


def test_health_shape():
    h = get_health()
    assert "services" in h
    assert "db_ok" in h
    assert isinstance(h["summary"], list)
    names = {s["service"] for s in h["services"]}
    assert "TourAPI" in names
    assert "CLOVA Studio" in names
