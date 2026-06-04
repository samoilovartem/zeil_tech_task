"""Run labeled queries through the full pipeline and report quality metrics."""

from __future__ import annotations

import json

from pathlib import Path

from zeil.config import settings
from zeil.eval.metrics import mrr, ndcg_at_k, precision_at_k, recall_at_k
from zeil.location.normalize import Gazetteer
from zeil.query.retrieve import retrieve
from zeil.query.understand import understand
from zeil.rank.geo import apply_proximity
from zeil.rank.model import Experience
from zeil.rank.score import score_candidate


def _rank(query: str, gz: Gazetteer, proximity_km=None) -> list[str]:
    intent = understand(query, proximity_km=proximity_km)
    docs = retrieve(intent, gz)
    scored = []
    for d in docs:
        exps = [
            Experience(
                **{
                    k: e[k]
                    for k in (
                        'title',
                        'company',
                        'start_year',
                        'end_year',
                        'description',
                        'skills',
                        'seniority',
                        'domain',
                    )
                }
            )
            for e in d['experiences']
        ]
        bd = score_candidate(exps, intent)
        final = apply_proximity(bd.score, d, intent, gz)
        scored.append((d['_id'], final))
    scored.sort(key=lambda t: t[1], reverse=True)
    return [i for i, _ in scored]


def run(queries_path=None, k=settings.eval_k) -> list[dict]:
    queries_path = queries_path or settings.queries_path
    gz = Gazetteer.load(settings.gazetteer_path)
    rows = []
    for case in json.loads(Path(queries_path).read_text()):
        grades = {kk: int(vv) for kk, vv in case['judgments'].items()}
        relevant = {kk for kk, vv in grades.items() if vv >= settings.relevant_grade_min}
        ranked = _rank(case['query'], gz, case.get('proximity_km'))
        rows.append(
            {
                'query': case['query'],
                'p@k': round(precision_at_k(ranked, relevant, k), 3),
                'recall@k': round(recall_at_k(ranked, relevant, k), 3),
                'mrr': round(mrr(ranked, relevant), 3),
                'ndcg@k': round(ndcg_at_k(ranked, grades, k), 3),
            }
        )
    return rows


def print_report(rows: list[dict]) -> None:
    if not rows:
        print('no queries')
        return
    cols = ['query', 'p@k', 'recall@k', 'mrr', 'ndcg@k']
    print(f'{"query":50} {"p@k":>6} {"rec@k":>6} {"mrr":>6} {"ndcg":>6}')
    for r in rows:
        print(f'{r["query"][:50]:50} {r["p@k"]:>6} {r["recall@k"]:>6} {r["mrr"]:>6} {r["ndcg@k"]:>6}')
    agg = {c: round(sum(r[c] for r in rows) / len(rows), 3) for c in cols[1:]}
    print(f'{"AVERAGE":50} {agg["p@k"]:>6} {agg["recall@k"]:>6} {agg["mrr"]:>6} {agg["ndcg@k"]:>6}')
