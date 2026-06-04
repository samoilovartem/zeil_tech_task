from zeil.location.synonyms import apply_synonyms


def test_known_alias_maps_to_canonical_phrase():
    assert apply_synonyms('saigon') == 'ho chi minh city'
    assert apply_synonyms('nyc') == 'new york'


def test_unknown_passes_through_unchanged():
    assert apply_synonyms('parramatta') == 'parramatta'
