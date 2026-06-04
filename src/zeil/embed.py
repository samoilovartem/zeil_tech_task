"""Sentence-transformers wrapper (lazy-loaded). Model + dimension come from config."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from zeil.config import settings


@lru_cache(maxsize=1)
def _model():
    return SentenceTransformer(settings.embedding_model)


def embed(text: str) -> list[float]:
    return _model().encode(text, normalize_embeddings=True).tolist()
