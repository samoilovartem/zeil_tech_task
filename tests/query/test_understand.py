from zeil.query.understand import understand


def test_parses_seniority_skill_duration_and_domain():
    qi = understand('Senior backend engineer, 5+ years Python, financial services')
    assert qi.seniority_floor == 'senior'
    assert any(s.name == 'python' and s.min_years == 5 for s in qi.skills)
    assert qi.domain == 'financial_services'


def test_parses_location_and_proximity():
    qi = understand('truck driver near Parramatta', proximity_km=30)
    assert qi.location == 'Parramatta'
    assert qi.proximity_km == 30
