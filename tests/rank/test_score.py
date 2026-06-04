from zeil.rank.model import Experience, QueryIntent, SkillReq
from zeil.rank.score import score_candidate


def _candidate_c1():
    return [
        Experience(
            'Software Engineer',
            'Goldman Sachs',
            2018,
            2021,
            'Built trading APIs in Python and Java',
            ['python', 'java'],
            'mid',
            'financial_services',
        ),
        Experience(
            'Backend Lead',
            'Stripe',
            2021,
            2024,
            'Led payments infrastructure team, Python microservices',
            ['python'],
            'lead',
            'financial_services',
        ),
        Experience(
            'Freelance Developer', 'Freelance', 2016, 2018, 'Various web projects, mostly PHP', ['php'], 'mid', None
        ),
    ]


INTENT = QueryIntent(
    raw='Senior backend engineer, 5+ years Python, financial services',
    seniority_floor='senior',
    skills=[SkillReq('python', 5)],
    domain='financial_services',
)


def test_score_is_in_range_and_requirement_met():
    bd = score_candidate(_candidate_c1(), INTENT)
    assert 0 <= bd.score <= 100
    assert bd.requirements['python']['actual'] == 6
    assert bd.requirements['python']['met'] is True


def test_php_freelance_contributes_least():
    bd = score_candidate(_candidate_c1(), INTENT)
    contribs = {e['company']: e['contribution'] for e in bd.experiences}
    assert contribs['Freelance'] < contribs['Goldman Sachs']
    assert contribs['Freelance'] < contribs['Stripe']


def test_relevant_candidate_outranks_offdomain_one():
    c1 = score_candidate(_candidate_c1(), INTENT).score
    junior = [
        Experience(
            'Junior Developer',
            'SmallShop',
            2022,
            2024,
            'Django web apps in Python, some React',
            ['python', 'react', 'django'],
            'junior',
            None,
        )
    ]
    assert c1 > score_candidate(junior, INTENT).score


def test_breakdown_has_human_explanation():
    bd = score_candidate(_candidate_c1(), INTENT)
    assert isinstance(bd.explanation, list) and bd.explanation
