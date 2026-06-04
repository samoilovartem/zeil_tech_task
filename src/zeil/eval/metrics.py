"""Offline retrieval-quality metrics (pure functions)."""

from __future__ import annotations

import math


def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    return sum(1 for x in ranked[:k] if x in relevant) / k


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return sum(1 for x in ranked[:k] if x in relevant) / len(relevant)


def mrr(ranked: list[str], relevant: set[str]) -> float:
    for i, x in enumerate(ranked):
        if x in relevant:
            return 1.0 / (i + 1)
    return 0.0


def _dcg(grades: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades))


def ndcg_at_k(ranked: list[str], grades: dict[str, int], k: int) -> float:
    gains = [grades.get(x, 0) for x in ranked[:k]]
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = _dcg(ideal)
    return _dcg(gains) / idcg if idcg > 0 else 0.0
