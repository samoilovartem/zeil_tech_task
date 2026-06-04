from zeil.location.normalize import fold


def test_fold_strips_diacritics_and_lowercases():
    assert fold('Hà Nội') == 'ha noi'


def test_fold_collapses_separators_and_whitespace():
    assert fold('Vietnam - Hanoi') == 'vietnam hanoi'
    assert fold('  Ho Chi  Minh ') == 'ho chi minh'
