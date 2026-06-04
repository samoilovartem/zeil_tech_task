"""Central configuration via pydantic-settings — every tuning number in one place."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='zeil_', frozen=True)

    # ── OpenSearch connection & index ─────────────────────────────────────────
    opensearch_host: str = 'localhost'
    opensearch_port: int = 9200
    index_name: str = 'candidates'
    index_shards: int = 1
    index_replicas: int = 0

    # ── Embedding model ───────────────────────────────────────────────────────
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    embedding_dim: int = 384

    # ── Data files ────────────────────────────────────────────────────────────
    candidates_path: str = 'data/candidates.json'
    gazetteer_path: str = 'data/gazetteer.json'
    queries_path: str = 'data/eval/queries.json'

    # ── Location resolution (Part 2) ──────────────────────────────────────────
    level_confidence: dict[str, float] = {'suburb': 1.0, 'city': 0.9, 'region': 0.5, 'country': 0.2}
    unknown_location_confidence: float = 0.3

    # ── Relevance scoring / re-rank (Part 1) ──────────────────────────────────
    seniority_rank: dict[str, int] = {'junior': 1, 'mid': 2, 'senior': 3, 'lead': 4, 'principal': 5}
    # Signal weights inside one experience's relevance. Sum to 1.0.
    weight_skill: float = 0.45
    weight_domain: float = 0.35
    weight_seniority: float = 0.20
    # seniority_match output versus the required floor.
    seniority_score_meets: float = 1.0
    seniority_score_one_below: float = 0.5
    seniority_score_below: float = 0.2
    # recency_weight: weight halves every N years (bigger = slower decay).
    recency_halflife_years: float = 5.0
    # duration_weight = floor + (1 - floor) * min(1, years / cap).
    duration_floor: float = 0.6
    duration_cap_years: float = 4.0
    # Bonus added when an "N+ years skill" requirement is met.
    requirement_bonus: float = 0.5
    # Saturating normalisation to 0..scale: score = scale * raw / (raw + norm_k).
    score_scale: float = 100.0
    norm_k: float = 0.7
    # Experiences contributing below this are flagged "barely relevant".
    barely_relevant_threshold: float = 0.05
    # "Now" for recency math; pinned so scores/tests are deterministic.
    current_year: int = 2026

    # ── Geo proximity (Part 2 bonus) ──────────────────────────────────────────
    geo_fine_levels: frozenset[str] = frozenset({'suburb', 'city'})
    # Earth radius for the haversine great-circle distance (km).
    earth_radius_km: float = 6371.0
    # Gaussian decay scale used when a query does not specify its own proximity_km.
    default_proximity_scale_km: float = 25.0

    # ── Retrieval (Stage 1) ───────────────────────────────────────────────────
    rrf_k: int = 60
    retrieval_top_n: int = 200

    # ── Evaluation (Part 3) ───────────────────────────────────────────────────
    eval_k: int = 5
    relevant_grade_min: int = 2

    # ── CLI display ───────────────────────────────────────────────────────────
    # Default rows printed by `zeil search` (override per-run with --k). Presentation
    # only — distinct from eval_k, which is a metrics cutoff.
    search_top_k: int = 5


settings = Settings()
