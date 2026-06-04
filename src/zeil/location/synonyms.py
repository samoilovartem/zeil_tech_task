"""Curated alias map for non-diacritic location variants (folded keys)."""

SYNONYMS = {
    'saigon': 'ho chi minh city',
    'hcmc': 'ho chi minh city',
    'nyc': 'new york',
    'ny': 'new york',
}


def apply_synonyms(folded: str) -> str:
    """Map a folded location string through the alias table (identity if unknown)."""
    return SYNONYMS.get(folded, folded)
