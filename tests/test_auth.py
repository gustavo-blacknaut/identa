import pytest

from app.auth.passwords import hash_password, verify_password
from app.auth.throttle import LoginThrottle
from tests.conftest import PASSWORD, USERNAME, login


def test_password_hash_round_trip():
    password_hash = hash_password("uma-senha-forte")
    assert password_hash.startswith("$argon2")
    assert verify_password(password_hash, "uma-senha-forte")
    assert not verify_password(password_hash, "outra-senha")
    assert not verify_password(None, "qualquer")


def test_throttle_blocks_after_limit():
    throttle = LoginThrottle(max_attempts=3, window_seconds=60)
    for _ in range(3):
        throttle.record_failure("ip:user")
    assert throttle.is_blocked("ip:user")
    throttle.reset("ip:user")
    assert not throttle.is_blocked("ip:user")


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/"), ("get", "/novo"), ("get", "/documentos/1"), ("get", "/imagens/1/original")],
)
def test_pages_redirect_to_login_when_anonymous(client, method, path):
    response = getattr(client, method)(path, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


@pytest.mark.parametrize("path", ["/documentos", "/documentos/1/excluir", "/pessoas/1/excluir", "/documentos/1/reprocessar"])
def test_mutations_are_rejected_when_anonymous(client, path):
    assert client.post(path).status_code == 401


def test_wrong_password_is_rejected(client):
    response = client.post("/login", data={"username": USERNAME, "password": "senha-errada"})
    assert response.status_code == 401
    assert "inválidos" in response.text


def test_login_and_logout(client):
    login(client)
    assert client.get("/", follow_redirects=False).status_code == 200
    client.post("/logout")
    assert client.get("/", follow_redirects=False).status_code == 303


def test_login_is_throttled(client):
    for _ in range(5):
        client.post("/login", data={"username": USERNAME, "password": "senha-errada"})
    response = client.post("/login", data={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 429


def test_session_cookie_is_strict_and_http_only(client):
    response = login(client)
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
