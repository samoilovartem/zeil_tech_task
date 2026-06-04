"""Shared data structures for query intent and scoring."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkillReq:
    name: str
    min_years: float = 0.0


@dataclass
class QueryIntent:
    raw: str
    seniority_floor: str | None = None
    skills: list[SkillReq] = field(default_factory=list)
    domain: str | None = None
    location: str | None = None
    proximity_km: float | None = None  # set when the role is proximity-critical


@dataclass
class Experience:
    title: str
    company: str
    start_year: int
    end_year: int | None  # None = ongoing ("present") role
    description: str
    skills: list[str]
    seniority: str
    domain: str | None
