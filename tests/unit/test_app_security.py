"""Regression tests for production-facing Flask security configuration."""

import pytest

from src.app.app import app, create_flask_app


def test_production_requires_session_secret(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_flask_app()


def test_production_security_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-only-production-secret")

    flask_app = create_flask_app()

    assert flask_app.config["SECRET_KEY"] == "test-only-production-secret"
    assert flask_app.config["WTF_CSRF_SECRET_KEY"] == "test-only-production-secret"
    assert flask_app.config["WTF_CSRF_CHECK_DEFAULT"] is True
    assert flask_app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert flask_app.config["SESSION_COOKIE_SECURE"] is True
    assert flask_app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_health_check_does_not_require_firebase():
    flask_app = create_flask_app()

    response = flask_app.test_client().get("/readyz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_request_fuse_rejects_before_route_handling(monkeypatch):
    monkeypatch.setenv("REQUEST_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("REQUEST_RATE_LIMIT_GLOBAL_PER_MINUTE", "2")
    monkeypatch.setenv("REQUEST_RATE_LIMIT_CLIENT_PER_MINUTE", "2")
    flask_app = create_flask_app()
    client = flask_app.test_client()

    assert client.get("/missing").status_code == 404
    assert client.get("/missing").status_code == 404

    response = client.get("/missing")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.headers["Cache-Control"] == "no-store"


def test_request_fuse_exempts_readiness_check(monkeypatch):
    monkeypatch.setenv("REQUEST_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("REQUEST_RATE_LIMIT_GLOBAL_PER_MINUTE", "1")
    monkeypatch.setenv("REQUEST_RATE_LIMIT_CLIENT_PER_MINUTE", "1")
    flask_app = create_flask_app()
    client = flask_app.test_client()

    assert client.get("/missing").status_code == 404
    assert client.get("/readyz").status_code == 200
    assert client.get("/readyz").status_code == 200


def test_auth_callback_rejects_request_without_csrf_token():
    response = app.test_client().post(
        "/auth_callback",
        json={"id_token": "not-a-real-token"},
    )

    assert response.status_code == 400
