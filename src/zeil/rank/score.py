"""Stage 2 re-ranker: explainable per-experience scoring + aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field

from zeil.config import settings
from zeil.rank.model import Experience, QueryIntent, SkillReq


def skill_match(e: Experience, req: SkillReq) -> float:
    return 1.0 if req.name in e.skills else 0.0


def domain_match(e: Experience, domain: str | None) -> float:
    if domain is None:
        return 0.0
    return 1.0 if e.domain == domain else 0.0


def seniority_match(e: Experience, floor: str | None) -> float:
    if floor is None:
        return settings.seniority_score_meets
    have = settings.seniority_rank.get(e.seniority, settings.seniority_rank['mid'])
    need = settings.seniority_rank.get(floor, settings.seniority_rank['senior'])
    if have >= need:
        return settings.seniority_score_meets
    if have == need - 1:
        return settings.seniority_score_one_below
    return settings.seniority_score_below


def _end_year(e: Experience) -> int:
    return e.end_year if e.end_year is not None else settings.current_year


def _start_year(e: Experience) -> int:
    return e.start_year if e.start_year is not None else _end_year(e)


def _years(e: Experience) -> int:
    return max(0, _end_year(e) - _start_year(e))


def recency_weight(e: Experience, current_year: int = settings.current_year) -> float:
    years_since = max(0, current_year - _end_year(e))
    # 0.5 is the definition of half-life: the weight halves every recency_halflife_years.
    return 0.5 ** (years_since / settings.recency_halflife_years)


def duration_weight(e: Experience) -> float:
    floor = settings.duration_floor
    return floor + (1 - floor) * min(1.0, _years(e) / settings.duration_cap_years)


@dataclass
class ScoreBreakdown:
    score: float
    requirements: dict
    experiences: list[dict]
    explanation: list[str] = field(default_factory=list)


def score_candidate(experiences: list[Experience], intent: QueryIntent) -> ScoreBreakdown:
    exp_rows, base = [], 0.0
    for e in experiences:
        skill = max((skill_match(e, s) for s in intent.skills), default=0.0)
        dom = domain_match(e, intent.domain)
        sen = seniority_match(e, intent.seniority_floor)
        rec = recency_weight(e)
        dur = duration_weight(e)
        relevance = settings.weight_skill * skill + settings.weight_domain * dom + settings.weight_seniority * sen
        contribution = relevance * rec * dur
        base += contribution
        exp_rows.append(
            {
                'company': e.company,
                'title': e.title,
                'contribution': round(contribution, 4),
                'signals': {
                    'skill': skill,
                    'domain': dom,
                    'seniority': sen,
                    'recency': round(rec, 3),
                    'duration': round(dur, 3),
                },
            }
        )

    # Requirement gate: accumulate skill-years evidence across roles.
    requirements, bonus = {}, 0.0
    for s in intent.skills:
        if s.min_years > 0:
            actual = sum(_years(e) for e in experiences if s.name in e.skills)
            met = actual >= s.min_years
            requirements[s.name] = {'required': s.min_years, 'actual': actual, 'met': met}
            if met:
                bonus += settings.requirement_bonus

    raw = base + bonus
    score = round(settings.score_scale * raw / (raw + settings.norm_k), 1)

    explanation = []
    for name, r in requirements.items():
        explanation.append(
            f'{"Met" if r["met"] else "Missed"} {name} {r["required"]}+ years ({r["actual"]} across roles)'
        )
    top = max(exp_rows, key=lambda r: r['contribution']) if exp_rows else None
    if top:
        explanation.append(f'Strongest role: {top["title"]} at {top["company"]}')
    weak = [r for r in exp_rows if r['contribution'] < settings.barely_relevant_threshold]
    for r in weak:
        explanation.append(f'{r["company"]} role barely relevant to this search')
    return ScoreBreakdown(score, requirements, exp_rows, explanation)
