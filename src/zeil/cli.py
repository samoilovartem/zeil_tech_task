"""CLI: ingest | search | eval | demo."""

from __future__ import annotations

import argparse

from zeil.config import settings
from zeil.eval.harness import print_report, run
from zeil.index.ingest import ingest
from zeil.location.normalize import Gazetteer
from zeil.query.retrieve import retrieve
from zeil.query.understand import understand
from zeil.rank.geo import apply_proximity
from zeil.rank.model import Experience
from zeil.rank.score import score_candidate


def _gz():
    return Gazetteer.load(settings.gazetteer_path)


def cmd_ingest(_):
    print('indexed', ingest())


def _search(query, proximity_km=None, k=settings.search_top_k):
    gz, intent = _gz(), understand(query, proximity_km=proximity_km)
    out = []
    for d in retrieve(intent, gz):
        exps = [
            Experience(
                **{
                    kk: e[kk]
                    for kk in (
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
        out.append((final, d['name'], bd))
    out.sort(key=lambda t: t[0], reverse=True)
    return out[:k]


def cmd_search(a):
    for final, name, bd in _search(a.query, a.proximity_km, a.k):
        print(f'\n{final:6.1f}  {name}')
        for line in bd.explanation:
            print(f'        - {line}')


def cmd_eval(_):
    print_report(run())


def cmd_demo(_):
    print('=== Part 1: relevance scoring ===')
    cmd_search(
        argparse.Namespace(query='Senior backend engineer, 5+ years Python, financial services', proximity_km=None, k=3)
    )
    print('\n=== Part 2: suburb proximity (truck drivers near Parramatta) ===')
    cmd_search(argparse.Namespace(query='truck driver near Parramatta', proximity_km=30, k=6))


def main():
    p = argparse.ArgumentParser(prog='zeil')
    sub = p.add_subparsers(required=True)
    sub.add_parser('ingest').set_defaults(func=cmd_ingest)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--proximity-km', type=float, default=None)
    s.add_argument('--k', type=int, default=settings.search_top_k)
    s.set_defaults(func=cmd_search)
    sub.add_parser('eval').set_defaults(func=cmd_eval)
    sub.add_parser('demo').set_defaults(func=cmd_demo)
    a = p.parse_args()
    a.func(a)


if __name__ == '__main__':
    main()
