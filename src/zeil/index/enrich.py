"""Deterministic per-experience enrichment: skills, seniority, domain."""

from __future__ import annotations

import re

SKILL_VOCAB = ['python', 'java', 'php', 'react', 'django', 'go', 'rust', 'scala', 'kubernetes']

_SENIORITY_RULES = [
    ('principal', 'principal'),
    ('staff', 'lead'),
    ('lead', 'lead'),
    ('head', 'lead'),
    ('senior', 'senior'),
    ('sr', 'senior'),
    ('junior', 'junior'),
    ('jr', 'junior'),
    ('intern', 'junior'),
]

# Known employers → industry, plus keyword hints. Explainable on purpose.
COMPANY_INDUSTRY = {
    'goldman sachs': 'financial_services',
    'stripe': 'financial_services',
    'dbs bank': 'financial_services',
    'jpmorgan': 'financial_services',
    'revolut': 'financial_services',
    'paypal': 'financial_services',
}
DOMAIN_KEYWORDS = {
    'financial_services': ['trading', 'payments', 'banking', 'fintech', 'risk', 'settlement'],
    'healthcare': ['clinical', 'patient', 'ehr', 'medical'],
}


def extract_skills(text: str) -> list[str]:
    low = text.lower()
    return [s for s in SKILL_VOCAB if re.search(rf'\b{s}\b', low)]


def extract_seniority(title: str) -> str:
    low = title.lower()
    for needle, level in _SENIORITY_RULES:
        if re.search(rf'\b{needle}\b', low):
            return level
    return 'mid'  # default for "Engineer"/"Developer" with no modifier


def extract_domain(company: str, description: str) -> str | None:
    c = company.lower().strip()
    if c in COMPANY_INDUSTRY:
        return COMPANY_INDUSTRY[c]
    text = description.lower()
    for domain, kws in DOMAIN_KEYWORDS.items():
        if any(re.search(rf'\b{kw}\b', text) for kw in kws):
            return domain
    return None
