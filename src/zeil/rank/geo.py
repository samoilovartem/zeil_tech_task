"""Geo proximity: distance, decay, and how proximity reshapes the score by intent."""

from __future__ import annotations

import math

from zeil.config import settings
from zeil.location.normalize import Gazetteer
from zeil.rank.model import QueryIntent


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = settings.earth_radius_km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def proximity_decay(distance_km: float, scale_km: float = settings.default_proximity_scale_km) -> float:
    """Gaussian-ish decay in [0,1]: 1.0 at the target, ~0 far away."""
    if scale_km <= 0:
        return 1.0 if distance_km == 0 else 0.0
    return math.exp(-(distance_km**2) / (2 * scale_km**2))


def apply_proximity(base_score: float, doc: dict, intent: QueryIntent, gz: Gazetteer) -> float:
    # Remote-friendly search: location is not a ranking factor.
    if intent.proximity_km is None or not intent.location:
        return base_score
    target = gz.resolve(intent.location)
    if target.lat is None:
        return base_score
    # Proximity-critical: vague profiles can't be trusted → exclude.
    if doc.get('location_level') not in settings.geo_fine_levels:
        return 0.0
    point = doc.get('location_point')
    if not point:
        return 0.0
    dist = haversine_km(target.lat, target.lon, point['lat'], point['lon'])
    decay = proximity_decay(dist, scale_km=intent.proximity_km)
    # Location dominates for this role: multiply base by proximity.
    return round(base_score * decay, 2)
