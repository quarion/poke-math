"""Tests for the dependency-free request fuse."""

from src.app.security.rate_limiter import (
    RateLimit,
    RequestRateLimiter,
    client_identifier,
)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_global_limit_cannot_be_bypassed_by_rotating_clients():
    clock = Clock()
    limiter = RequestRateLimiter(clock=clock)
    limit = RateLimit("all", global_limit=2, client_limit=10)

    assert limiter.check("client-a", [limit]).allowed
    assert limiter.check("client-b", [limit]).allowed

    decision = limiter.check("client-c", [limit])
    assert not decision.allowed
    assert decision.retry_after == 60


def test_client_limit_does_not_block_a_different_client():
    limiter = RequestRateLimiter(clock=Clock())
    limit = RateLimit("all", global_limit=10, client_limit=1)

    assert limiter.check("client-a", [limit]).allowed
    assert not limiter.check("client-a", [limit]).allowed
    assert limiter.check("client-b", [limit]).allowed


def test_sliding_window_releases_capacity_after_expiry():
    clock = Clock()
    limiter = RequestRateLimiter(clock=clock)
    limit = RateLimit("all", global_limit=1, client_limit=1)

    assert limiter.check("client-a", [limit]).allowed
    clock.now = 59.1
    assert limiter.check("client-a", [limit]).retry_after == 1
    clock.now = 60.0
    assert limiter.check("client-a", [limit]).allowed


def test_client_bucket_bound_does_not_evict_global_counter():
    limiter = RequestRateLimiter(max_client_buckets=1, clock=Clock())
    limit = RateLimit("all", global_limit=2, client_limit=2)

    assert limiter.check("client-a", [limit]).allowed
    assert limiter.check("client-b", [limit]).allowed
    assert not limiter.check("client-c", [limit]).allowed


def test_client_identifier_uses_forwarded_address_only_when_trusted():
    assert client_identifier(
        "10.0.0.1",
        "203.0.113.9, 198.51.100.2",
        trust_forwarded_for=True,
    ) == "203.0.113.9"
    assert client_identifier(
        "10.0.0.1",
        "203.0.113.9",
        trust_forwarded_for=False,
    ) == "10.0.0.1"


def test_client_identifier_ignores_invalid_addresses():
    assert client_identifier(
        "192.0.2.4",
        "not-an-ip",
        trust_forwarded_for=True,
    ) == "192.0.2.4"
