from zeil.location.normalize import Gazetteer

GZ = Gazetteer.load('data/gazetteer.json')


def test_all_hanoi_variants_resolve_to_same_place():
    a = GZ.resolve('Hà Nội')
    b = GZ.resolve('Ha noi')
    c = GZ.resolve('Vietnam - Hanoi')
    assert a.id == b.id == c.id == 'vn-hanoi'
    assert a.level == 'city'


def test_suburb_has_fine_granularity_and_coords():
    p = GZ.resolve('Parramatta')
    assert p.id == 'au-parramatta'
    assert p.level == 'suburb'
    assert p.lat is not None and p.lon is not None


def test_vague_country_resolves_with_coarse_granularity():
    p = GZ.resolve('Australia')
    assert p.id == 'au'
    assert p.level == 'country'


def test_unknown_location_returns_unresolved():
    p = GZ.resolve('Atlantis')
    assert p.id is None
    assert p.level == 'unresolved'
    assert p.confidence == 0.0
