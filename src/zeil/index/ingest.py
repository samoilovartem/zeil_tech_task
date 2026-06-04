"""Load candidates → enrich → resolve location → embed → bulk index."""

from __future__ import annotations

import json

from pathlib import Path

from opensearchpy.helpers import bulk

from zeil.client import get_client
from zeil.config import settings
from zeil.embed import embed
from zeil.index.enrich import extract_domain, extract_seniority, extract_skills
from zeil.index.mappings import INDEX_BODY
from zeil.location.normalize import Gazetteer


def build_doc(candidate: dict, gz: Gazetteer) -> dict:
    exps = []
    text_parts = []
    for e in candidate['experiences']:
        exps.append(
            {
                **e,
                'skills': extract_skills(e['description'] + ' ' + e['title']),
                'seniority': extract_seniority(e['title']),
                'domain': extract_domain(e['company'], e['description']),
            }
        )
        text_parts.append(f'{e["title"]} at {e["company"]}: {e["description"]}')
    loc = gz.resolve(candidate.get('location_raw', ''))
    doc = {
        'name': candidate['name'],
        'location_raw': candidate.get('location_raw', ''),
        'location_id': loc.id,
        'location_level': loc.level,
        'location_confidence': loc.confidence,
        'experiences': exps,
        'profile_embedding': embed(' \n '.join(text_parts)),
    }
    if loc.lat is not None:
        doc['location_point'] = {'lat': loc.lat, 'lon': loc.lon}
    return doc


def recreate_index(client) -> None:
    if client.indices.exists(index=settings.index_name):
        client.indices.delete(index=settings.index_name)
    client.indices.create(index=settings.index_name, body=INDEX_BODY)


def ingest(candidates_path: str | None = None, gazetteer_path: str | None = None) -> int:
    candidates_path = candidates_path or settings.candidates_path
    gazetteer_path = gazetteer_path or settings.gazetteer_path
    client = get_client()
    gz = Gazetteer.load(gazetteer_path)
    candidates = json.loads(Path(candidates_path).read_text())
    recreate_index(client)
    actions = [{'_index': settings.index_name, '_id': c['id'], '_source': build_doc(c, gz)} for c in candidates]
    ok, _ = bulk(client, actions, refresh=True)
    return ok
