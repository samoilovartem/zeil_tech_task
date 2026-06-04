"""Shared Stage-2 ranking: rebuild Experience objects from retrieved docs, score
them, apply geo proximity, and return them sorted best-first.

Used by BOTH the CLI search command and the eval harness, so what `zeil eval`
measures is exactly what `zeil search` produces — no drift between the two.
"""

from __future__ import annotations

from dataclasses import fields

from zeil.location.normalize import Gazetteer
from zeil.rank.geo import apply_proximity
from zeil.rank.model import Experience, QueryIntent
from zeil.rank.score import ScoreBreakdown, score_candidate

# Field set is derived from the dataclass, so adding an Experience field updates both
# call sites automatically (no hardcoded key tuple to keep in sync).
_EXP_FIELDS = tuple(f.name for f in fields(Experience))


def _experiences(doc: dict) -> list[Experience]:
    return [Experience(**{k: e[k] for k in _EXP_FIELDS}) for e in doc['experiences']]


def rank_docs(intent: QueryIntent, docs: list[dict], gz: Gazetteer) -> list[tuple[dict, ScoreBreakdown, float]]:
    ranked = []
    for d in docs:
        bd = score_candidate(_experiences(d), intent)
        final = apply_proximity(bd.score, d, intent, gz)
        ranked.append((d, bd, final))
    ranked.sort(key=lambda t: t[2], reverse=True)
    return ranked
