"""Rule-based query understanding → QueryIntent.
Production note (write-up): an LLM or learned parser replaces these rules at scale."""

from __future__ import annotations

import re

from zeil.index.enrich import SKILL_VOCAB
from zeil.rank.model import QueryIntent, SkillReq

_SENIORITY = ['principal', 'lead', 'senior', 'junior']
_DOMAIN_PHRASES = {
    'financial services': 'financial_services',
    'fintech': 'financial_services',
    'payments': 'financial_services',
    'banking': 'financial_services',
    'healthcare': 'healthcare',
}


def understand(query: str, proximity_km: float | None = None) -> QueryIntent:
    low = query.lower()
    qi = QueryIntent(raw=query, proximity_km=proximity_km)

    for level in _SENIORITY:
        if re.search(rf'\b{level}\b', low):
            qi.seniority_floor = level
            break

    for skill in SKILL_VOCAB:
        m = re.search(rf'(\d+)\s*\+?\s*years?\s+{skill}\b', low)
        if m:
            qi.skills.append(SkillReq(skill, float(m.group(1))))
        elif re.search(rf'\b{skill}\b', low):
            qi.skills.append(SkillReq(skill))

    for phrase, domain in _DOMAIN_PHRASES.items():
        if phrase in low:
            qi.domain = domain
            break

    # Capture 1–3 words after near/around/in, case-insensitive. The gazetteer then
    # decides validity, so an over-capture degrades to "unresolved" rather than a crash.
    m = re.search(r'\b(?:near|around|in)\s+([A-Za-z]+(?:[\s-][A-Za-z]+){0,2})', query, re.IGNORECASE)
    if m:
        qi.location = m.group(1).strip()
    return qi
