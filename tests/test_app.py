import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_healthcheck(client):
    response = client.get('/healthcheck')
    assert response.status_code == 200
    assert b"ok" in response.data

