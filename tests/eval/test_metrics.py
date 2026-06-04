from zeil.eval.metrics import mrr, ndcg_at_k, precision_at_k, recall_at_k


def test_precision_and_recall():
    ranked = ['a', 'b', 'c', 'd']
    relevant = {'a', 'c', 'x'}
    assert precision_at_k(ranked, relevant, 4) == 0.5  # 2 of top4 relevant
    assert recall_at_k(ranked, relevant, 4) == 2 / 3  # found 2 of 3 relevant


def test_mrr_uses_first_hit_rank():
    assert mrr(['x', 'a', 'b'], {'a'}) == 0.5  # first hit at rank 2


def test_ndcg_perfect_order_is_one():
    ranked = ['a', 'b', 'c']
    grades = {'a': 3, 'b': 2, 'c': 1}
    assert abs(ndcg_at_k(ranked, grades, 3) - 1.0) < 1e-9


def test_ndcg_penalizes_bad_order():
    grades = {'a': 3, 'b': 2, 'c': 1}
    good = ndcg_at_k(['a', 'b', 'c'], grades, 3)
    bad = ndcg_at_k(['c', 'b', 'a'], grades, 3)
    assert bad < good
