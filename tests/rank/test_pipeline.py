from zeil.location.normalize import Gazetteer
from zeil.rank.model import QueryIntent, SkillReq
from zeil.rank.pipeline import rank_docs

GZ = Gazetteer.load('data/gazetteer.json')


def _exp(**kw):
    base = dict(
        title='Engineer',
        company='X',
        start_year=2020,
        end_year=2024,
        description='',
        skills=[],
        seniority='senior',
        domain=None,
    )
    base.update(kw)
    return base


def _doc(_id, name, experiences):
    return {
        '_id': _id,
        'name': name,
        'experiences': experiences,
        'location_level': 'unresolved',
        'location_point': None,
    }


def test_rank_docs_sorts_by_score_descending():
    intent = QueryIntent(raw='python', skills=[SkillReq('python')])
    docs = [
        _doc('b', 'B', [_exp(skills=['php'], description='php')]),
        _doc('a', 'A', [_exp(skills=['python'], description='python')]),
    ]
    ranked = rank_docs(intent, docs, GZ)
    assert [d['_id'] for d, _bd, _final in ranked] == ['a', 'b']
    # rank_docs returns (doc, ScoreBreakdown, final_score) triples, sorted desc.
    assert ranked[0][2] >= ranked[1][2]
