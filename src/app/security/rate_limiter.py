"""Small in-process request fuse for the single-instance Cloud Run service."""

from __future__ import annotations

import math
import time
from collections import OrderedDict, deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from ipaddress import ip_address
from threading import Lock


@dataclass(frozen=True)
class RateLimit:
    """One sliding-window limit applied to a request."""

    scope: str
    global_limit: int
    client_limit: int
    window_seconds: int = 60


@dataclass(frozen=True)
class RateLimitDecision:
    """Result returned by :class:`RequestRateLimiter`."""

    allowed: bool
    retry_after: int = 0


class RequestRateLimiter:
    """Thread-safe sliding-window limiter with bounded client state.

    Global counters are never evicted, so rotating client identities cannot
    bypass the cost fuse. Client counters are best-effort isolation and use a
    bounded LRU map to prevent an identity-cardinality memory attack.
    """

    def __init__(
        self,
        *,
        max_client_buckets: int = 4096,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_client_buckets < 1:
            raise ValueError("max_client_buckets must be positive")
        self._max_client_buckets = max_client_buckets
        self._clock = clock
        self._lock = Lock()
        self._global: dict[str, deque[float]] = {}
        self._clients: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()

    def check(
        self,
        client_id: str,
        limits: Iterable[RateLimit],
    ) -> RateLimitDecision:
        """Atomically evaluate and consume every supplied limit."""

        requested_limits = tuple(limits)
        now = self._clock()

        with self._lock:
            counters: list[tuple[deque[float], int, int]] = []
            for limit in requested_limits:
                if limit.global_limit < 1 or limit.client_limit < 1:
                    raise ValueError("rate limits must be positive")

                global_counter = self._global.setdefault(limit.scope, deque())
                client_counter = self._client_counter(limit.scope, client_id)
                self._prune(global_counter, now, limit.window_seconds)
                self._prune(client_counter, now, limit.window_seconds)
                counters.extend(
                    (
                        (global_counter, limit.global_limit, limit.window_seconds),
                        (client_counter, limit.client_limit, limit.window_seconds),
                    )
                )

            retry_after = 0
            for counter, threshold, window_seconds in counters:
                if len(counter) >= threshold:
                    retry_after = max(
                        retry_after,
                        max(1, math.ceil(counter[0] + window_seconds - now)),
                    )

            if retry_after:
                return RateLimitDecision(False, retry_after)

            for counter, _threshold, _window_seconds in counters:
                counter.append(now)
            return RateLimitDecision(True)

    def _client_counter(self, scope: str, client_id: str) -> deque[float]:
        key = (scope, client_id)
        counter = self._clients.get(key)
        if counter is not None:
            self._clients.move_to_end(key)
            return counter

        while len(self._clients) >= self._max_client_buckets:
            self._clients.popitem(last=False)
        counter = deque()
        self._clients[key] = counter
        return counter

    @staticmethod
    def _prune(counter: deque[float], now: float, window_seconds: int) -> None:
        cutoff = now - window_seconds
        while counter and counter[0] <= cutoff:
            counter.popleft()


def client_identifier(
    remote_addr: str | None,
    forwarded_for: str | None,
    *,
    trust_forwarded_for: bool,
) -> str:
    """Return a normalized best-effort client address.

    Cloud Run places the original client first in ``X-Forwarded-For``. The
    header is used only in production, where requests reach the app through
    Google's proxy. This identity is not a security boundary: the non-evictable
    global counter remains authoritative if a client can vary the header.
    """

    candidates = []
    if trust_forwarded_for and forwarded_for:
        candidates.extend(part.strip() for part in forwarded_for.split(","))
    if remote_addr:
        candidates.append(remote_addr.strip())

    for candidate in candidates:
        try:
            return ip_address(candidate).compressed
        except ValueError:
            continue
    return "unknown"
