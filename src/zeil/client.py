"""OpenSearch client factory. Host, port and index name come from config."""

from opensearchpy import OpenSearch

from zeil.config import settings


def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{'host': settings.opensearch_host, 'port': settings.opensearch_port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )
