"""Index settings + mappings: analyzers, nested experiences, knn_vector, geo_point."""

from zeil.config import settings

INDEX_BODY = {
    'settings': {
        'index': {
            'knn': True,
            'number_of_shards': settings.index_shards,
            'number_of_replicas': settings.index_replicas,
        },
        'analysis': {
            'analyzer': {
                'folding': {'type': 'custom', 'tokenizer': 'standard', 'filter': ['lowercase', 'asciifolding']}
            }
        },
    },
    'mappings': {
        'properties': {
            'name': {'type': 'text'},
            'location_raw': {'type': 'text', 'analyzer': 'folding'},
            'location_id': {'type': 'keyword'},
            'location_level': {'type': 'keyword'},
            'location_point': {'type': 'geo_point'},
            'location_confidence': {'type': 'float'},
            'profile_embedding': {
                'type': 'knn_vector',
                'dimension': settings.embedding_dim,
                'method': {'name': 'hnsw', 'space_type': 'cosinesimil', 'engine': 'lucene'},
            },
            'experiences': {
                'type': 'nested',
                'properties': {
                    'title': {'type': 'text', 'analyzer': 'folding'},
                    'company': {'type': 'text', 'fields': {'raw': {'type': 'keyword'}}},
                    'description': {'type': 'text', 'analyzer': 'folding'},
                    'start_year': {'type': 'integer'},
                    'end_year': {'type': 'integer'},
                    'skills': {'type': 'keyword'},
                    'seniority': {'type': 'keyword'},
                    'domain': {'type': 'keyword'},
                },
            },
        }
    },
}
