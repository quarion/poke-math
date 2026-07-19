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


def test_auth_callback_rejects_request_without_csrf_token():
    response = app.test_client().post(
        "/auth_callback",
        json={"id_token": "not-a-real-token"},
    )

    assert response.status_code == 400
