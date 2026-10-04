import pytest
from fastapi.testclient import TestClient

from identa.config import ConfigurationError, get_settings, load_settings
from identa.main import create_app
from identa.security.crypto import generate_key


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_refuses_to_start_without_encryption_key(monkeypatch):
    monkeypatch.setenv("IDENTA_SECRET_KEY", generate_key())
    with pytest.raises(ConfigurationError) as error:
        load_settings(_env_file=None)
    assert "IDENTA_ENCRYPTION_KEY" in str(error.value)


def test_encryption_can_be_disabled(monkeypatch):
    monkeypatch.setenv("IDENTA_SECRET_KEY", generate_key())
    monkeypatch.setenv("IDENTA_ENCRYPTION_ENABLED", "false")
    assert load_settings(_env_file=None).encryption_enabled is False


def test_refuses_short_secret_key_with_variable_name(monkeypatch):
    monkeypatch.setenv("IDENTA_ENCRYPTION_KEY", generate_key())
    monkeypatch.setenv("IDENTA_SECRET_KEY", "short")
    with pytest.raises(ConfigurationError) as error:
        load_settings(_env_file=None)
    assert "IDENTA_SECRET_KEY" in str(error.value)


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        ("IDENTA_DATABASE_URL", "mysql://x", "IDENTA_DATABASE_URL"),
        ("IDENTA_UPLOAD_FORMATS", "jpeg,gif", "IDENTA_UPLOAD_FORMATS"),
        ("IDENTA_OCR_DEVICE", "tpu", "IDENTA_OCR_DEVICE"),
        ("IDENTA_UPLOAD_MAX_MB", "0", "IDENTA_UPLOAD_MAX_MB"),
        ("IDENTA_PUBLIC_URL", "identa.local", "IDENTA_PUBLIC_URL"),
        ("IDENTA_SMTP_HOST", "smtp.exemplo.com", "IDENTA_SMTP_FROM"),
    ],
)
def test_invalid_values_are_reported_by_variable(monkeypatch, name, value, expected):
    monkeypatch.setenv("IDENTA_ENCRYPTION_KEY", generate_key())
    monkeypatch.setenv("IDENTA_SECRET_KEY", generate_key())
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError) as error:
        load_settings(_env_file=None)
    assert expected in str(error.value)


def test_postgres_url_uses_psycopg(monkeypatch):
    monkeypatch.setenv("IDENTA_ENCRYPTION_KEY", generate_key())
    monkeypatch.setenv("IDENTA_SECRET_KEY", generate_key())
    monkeypatch.setenv("IDENTA_DATABASE_URL", "postgresql://identa:senha@db:5432/identa")
    assert load_settings(_env_file=None).database_url.startswith("postgresql+psycopg://")


def test_health_endpoint_is_public(monkeypatch, tmp_path):
    monkeypatch.setenv("IDENTA_ENCRYPTION_KEY", generate_key())
    monkeypatch.setenv("IDENTA_SECRET_KEY", generate_key())
    monkeypatch.setenv("IDENTA_DATABASE_URL", f"sqlite:///{tmp_path / 'health.db'}")
    response = TestClient(create_app(load_settings(_env_file=None))).get("/health")
    assert response.json() == {"status": "ok"}


def test_api_does_not_serve_frontend(client):
    assert client.get("/").status_code == 404
    assert client.get("/pessoas").status_code == 404
