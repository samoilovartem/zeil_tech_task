import pytest

from zeil.client import get_client


@pytest.fixture(scope='session')
def os_client():
    client = get_client()
    try:
        client.cluster.health(request_timeout=2)
    except Exception:
        pytest.skip('OpenSearch not reachable on localhost:9200')
    return client
