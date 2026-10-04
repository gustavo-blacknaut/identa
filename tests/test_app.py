import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import MissingSecretKeyError, create_app
from app.security.crypto import EncryptionKeyError, generate_key


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_app_refuses_to_start_without_encryption_key(monkeypatch):
    monkeypatch.setenv("GREEN_OCR_ENCRYPTION_KEY", "")
    with pytest.raises(EncryptionKeyError):
        create_app()


def test_app_refuses_to_start_without_secret_key(monkeypatch):
    monkeypatch.setenv("GREEN_OCR_ENCRYPTION_KEY", generate_key())
    monkeypatch.setenv("GREEN_OCR_SECRET_KEY", "short")
    with pytest.raises(MissingSecretKeyError):
        create_app()


def test_health_endpoint_is_public(monkeypatch):
    monkeypatch.setenv("GREEN_OCR_ENCRYPTION_KEY", generate_key())
    monkeypatch.setenv("GREEN_OCR_SECRET_KEY", generate_key())
    response = TestClient(create_app()).get("/health")
    assert response.json() == {"status": "ok"}
