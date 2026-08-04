from BE.services.health import get_health


def test_health_shape():
    h = get_health()
    assert "services" in h
    assert "db_ok" in h
    assert "readiness" in h
    assert "setup_hints" in h
    assert isinstance(h["summary"], list)
    names = {s["service"] for s in h["services"]}
    assert "TourAPI" in names
    assert "CLOVA Studio" in names
    assert "NAVER Maps JS" in names
    assert "NAVER Maps Geocode" in names


def test_health_probe_without_keys():
    h = get_health(probe=True)
    assert isinstance(h.get("probes"), list)
    assert len(h["probes"]) >= 3
