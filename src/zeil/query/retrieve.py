"""Stage 1 retrieval: lexical (BM25) + semantic (kNN), fused with RRF, + location filter.
Production note (write-up): OpenSearch's native `hybrid` query + normalization-processor
search pipeline does this in-engine; here we fuse in Python for transparency."""

from __future__ import annotations

from zeil.client import get_client
from zeil.config import settings
from zeil.embed import embed
from zeil.location.normalize import Gazetteer
from zeil.rank.model import QueryIntent


def _location_filter(intent: QueryIntent, gz: Gazetteer) -> list[dict]:
    if not intent.location:
        return []
    loc = gz.resolve(intent.location)
    if loc.id is None:
        return []
    return [{'term': {'location_id': loc.id}}] if intent.proximity_km is None else []


def _rrf(rankings: list[list[str]], k: int = settings.rrf_k) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, _id in enumerate(ranking):
            scores[_id] = scores.get(_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


def retrieve(intent: QueryIntent, gz: Gazetteer, top_n: int = settings.retrieval_top_n) -> list[dict]:
    client = get_client()
    filt = _location_filter(intent, gz)

    # Lexical: match query text across nested experience fields.
    skill_terms = ' '.join(s.name for s in intent.skills)
    lexical_text = f'{intent.raw} {skill_terms}'.strip()
    lexical = {
        'bool': {
            'filter': filt,
            'should': [
                {
                    'nested': {
                        'path': 'experiences',
                        'query': {
                            'multi_match': {
                                'query': lexical_text,
                                'fields': ['experiences.title', 'experiences.description'],
                            }
                        },
                    }
                }
            ],
            'minimum_should_match': 0,
        }
    }
    bm25 = client.search(index=settings.index_name, body={'size': top_n, '_source': False, 'query': lexical})
    bm25_ids = [h['_id'] for h in bm25['hits']['hits']]

    # Semantic: kNN over the profile embedding (filtered by location too).
    knn_query = {
        'knn': {
            'profile_embedding': {
                'vector': embed(intent.raw),
                'k': top_n,
                **({'filter': {'bool': {'filter': filt}}} if filt else {}),
            }
        }
    }
    sem = client.search(index=settings.index_name, body={'size': top_n, '_source': False, 'query': knn_query})
    sem_ids = [h['_id'] for h in sem['hits']['hits']]

    fused = _rrf([bm25_ids, sem_ids])
    ranked_ids = sorted(fused, key=fused.get, reverse=True)[:top_n]
    if not ranked_ids:
        return []
    docs = client.mget(index=settings.index_name, body={'ids': ranked_ids})['docs']
    return [d['_source'] | {'_id': d['_id']} for d in docs if d.get('found')]
