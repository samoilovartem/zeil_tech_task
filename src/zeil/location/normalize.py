"""Location normalization and gazetteer resolution."""

from __future__ import annotations

import re
import json
import unicodedata

from dataclasses import dataclass
from pathlib import Path

from zeil.config import settings
from zeil.location.synonyms import apply_synonyms

_SEP = re.compile(r'[^a-z0-9]+')


def fold(text: str) -> str:
    """Lowercase, strip diacritics (NFKD + drop combining marks), collapse separators."""
    if not text:
        return ''
    decomposed = unicodedata.normalize('NFKD', text)
    no_marks = ''.join(c for c in decomposed if not unicodedata.combining(c))
    lowered = no_marks.lower()
    return _SEP.sub(' ', lowered).strip()


@dataclass
class Resolved:
    id: str | None
    name: str | None
    level: str  # suburb|city|region|country|unresolved
    lat: float | None
    lon: float | None
    hierarchy: dict
    confidence: float
    raw: str


class Gazetteer:
    def __init__(self, entries: list[dict]):
        self._by_alias: dict[str, dict] = {}
        for e in entries:
            for alias in e['aliases']:
                self._by_alias[alias] = e

    @classmethod
    def load(cls, path: str | Path) -> Gazetteer:
        return cls(json.loads(Path(path).read_text()))

    def resolve(self, raw: str) -> Resolved:
        key = apply_synonyms(fold(raw))
        entry = self._by_alias.get(key)
        if entry is None:
            return Resolved(None, None, 'unresolved', None, None, {}, 0.0, raw)
        return Resolved(
            id=entry['id'],
            name=entry['name'],
            level=entry['level'],
            lat=entry.get('lat'),
            lon=entry.get('lon'),
            hierarchy=entry.get('hierarchy', {}),
            confidence=settings.level_confidence.get(entry['level'], settings.unknown_location_confidence),
            raw=raw,
        )
