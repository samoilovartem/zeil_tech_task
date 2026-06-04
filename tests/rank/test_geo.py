from zeil.location.normalize import Gazetteer
from zeil.rank.geo import apply_proximity, haversine_km, proximity_decay
from zeil.rank.model import QueryIntent

GZ = Gazetteer.load('data/gazetteer.json')


def test_haversine_known_distance():
    # Parramatta -> Harris Park is ~1 km
    d = haversine_km(-33.8150, 151.0011, -33.8230, 151.0050)
    assert 0 < d < 3


def test_decay_closer_scores_higher():
    assert proximity_decay(1, scale_km=25) > proximity_decay(20, scale_km=25)


def test_vague_country_profile_is_dropped_for_proximity_role():
    intent = QueryIntent(raw='truck driver near Parramatta', location='Parramatta', proximity_km=30)
    doc = {'location_level': 'country', 'location_point': None}
    assert apply_proximity(80.0, doc, intent, GZ) == 0.0  # too vague → excluded


def test_remote_role_keeps_base_score():
    intent = QueryIntent(raw='python developer', location=None, proximity_km=None)
    doc = {'location_level': 'country'}
    assert apply_proximity(80.0, doc, intent, GZ) == 80.0  # location is not a factor
