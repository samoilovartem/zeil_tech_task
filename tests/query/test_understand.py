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


def test_skill_token_not_matched_as_substring_of_another_word():
    qi = understand('3 years JavaScript developer')
    assert 'java' not in [s.name for s in qi.skills]


def test_location_extracted_case_insensitively():
    qi = understand('backend engineer in berlin')
    assert qi.location is not None and qi.location.lower() == 'berlin'


def test_location_capture_is_bounded():
    qi = understand('java dev in New York with react skills')
    assert len(qi.location.split()) <= 3
