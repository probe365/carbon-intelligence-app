import pytest
from app import app, generate_trial_key  # importa o app Flask e a função

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    #assert b"ok" in response.data



