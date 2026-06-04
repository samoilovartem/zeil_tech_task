from zeil.index.enrich import extract_domain, extract_seniority, extract_skills


def test_extract_skills_finds_python_case_insensitive():
    assert 'python' in extract_skills('Built trading APIs in Python and Java')
    assert 'java' in extract_skills('Built trading APIs in Python and Java')


def test_extract_skills_finds_php():
    assert extract_skills('Various web projects, mostly PHP') == ['php']


def test_seniority_from_title():
    assert extract_seniority('Backend Lead') == 'lead'
    assert extract_seniority('Senior Engineer') == 'senior'
    assert extract_seniority('Software Engineer') == 'mid'
    assert extract_seniority('Junior Developer') == 'junior'


def test_domain_from_company_and_keywords():
    assert extract_domain('Goldman Sachs', 'Built trading APIs') == 'financial_services'
    assert extract_domain('Stripe', 'payments infrastructure') == 'financial_services'
    assert extract_domain('SmallShop', 'Django web apps') is None


def test_company_match_handles_extra_tokens():
    assert extract_domain('Goldman Sachs Group', '') == 'financial_services'
    assert extract_domain('JPMorgan Chase & Co', '') == 'financial_services'


def test_generic_risk_word_is_not_financial_services():
    assert extract_domain('DevOps Co', 'reduced operational risk in CI pipelines') is None
