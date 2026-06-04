from zeil.rank.model import Experience, SkillReq
from zeil.rank.score import (
    domain_match,
    duration_weight,
    recency_weight,
    seniority_match,
    skill_match,
)


def exp(**kw):
    base = dict(
        title='Engineer',
        company='X',
        start_year=2020,
        end_year=2024,
        description='',
        skills=[],
        seniority='mid',
        domain=None,
    )
    base.update(kw)
    return Experience(**base)


def test_skill_match_present_vs_absent():
    assert skill_match(exp(skills=['python']), SkillReq('python')) == 1.0
    assert skill_match(exp(skills=['php']), SkillReq('python')) == 0.0


def test_domain_match():
    assert domain_match(exp(domain='financial_services'), 'financial_services') == 1.0
    assert domain_match(exp(domain=None), 'financial_services') == 0.0


def test_seniority_meets_floor_partial_and_below():
    assert seniority_match(exp(seniority='lead'), 'senior') == 1.0  # exceeds
    assert seniority_match(exp(seniority='mid'), 'senior') == 0.5  # one below
    assert seniority_match(exp(seniority='junior'), 'senior') == 0.2  # well below


def test_recency_weight_decays_with_age():
    recent = recency_weight(exp(end_year=2024), current_year=2026)
    old = recency_weight(exp(end_year=2018), current_year=2026)
    assert recent > old and 0 < old < recent <= 1.0


def test_duration_weight_rewards_longer_but_capped():
    short = duration_weight(exp(start_year=2023, end_year=2024))
    long = duration_weight(exp(start_year=2014, end_year=2024))
    assert long > short and long <= 1.0
