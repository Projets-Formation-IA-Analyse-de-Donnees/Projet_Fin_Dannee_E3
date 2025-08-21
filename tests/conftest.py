import pytest
from app import create_app

@pytest.fixture
def test_client(monkeypatch):
  
    monkeypatch.setattr('app.auth.API_KEY', 'super-secret-test-key')
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client