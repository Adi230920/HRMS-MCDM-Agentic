"""LLM client routing, resilient fallbacks, JSON validation, and call tracking."""

import json
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, TypeVar

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel

try:
    from app.config import settings
    from app.llm.models import (
        RouteLink,
        get_provider_endpoint,
        get_route_for_role,
    )
except ImportError:
    from backend.app.config import settings
    from backend.app.llm.models import (
        RouteLink,
        get_provider_endpoint,
        get_route_for_role,
    )

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM errors."""


class EmptyReplyError(LLMError, ValueError):
    """Raised when an LLM returns an empty content response."""

    def __init__(self, message: str, finish_reason: str | None = None) -> None:
        super().__init__(message)
        self.finish_reason = finish_reason


class AllLinksFailedError(LLMError, RuntimeError):
    """Raised when all provider links in a route chain fail."""


@dataclass
class CallRecord:
    """Record of an individual LLM call attempt."""

    role: str
    provider: str
    model: str
    tokens: int
    latency: float
    finish_reason: str | None
    retries: int
    error: str | None
    timestamp: float = field(default_factory=time.time)


CALL_LOG: list[CallRecord] = []
_SEMAPHORE = threading.Semaphore(settings.MAX_CONCURRENCY)
_CLIENT_CACHE: dict[tuple[str, str], OpenAI] = {}


def get_call_log() -> list[CallRecord]:
    """Retrieve the in-memory call log."""
    return list(CALL_LOG)


def clear_call_log() -> None:
    """Clear the in-memory call log."""
    CALL_LOG.clear()


def get_client(provider: str) -> OpenAI:
    """Obtain or cache an OpenAI client instance for a provider."""
    base_url, api_key = get_provider_endpoint(provider)
    cache_key = (base_url, api_key)
    if cache_key not in _CLIENT_CACHE:
        _CLIENT_CACHE[cache_key] = OpenAI(
            base_url=base_url,
            api_key=api_key or "no-key-set",
            timeout=30.0,
        )
    return _CLIENT_CACHE[cache_key]


def _extract_json(text: str) -> Any:
    """Find the outermost curly braces to ignore conversational text before or after."""
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("no JSON object in reply")
    cleaned = text[a : b + 1]
    return json.loads(cleaned)


def _is_failover_error(exc: Exception) -> bool:
    """Check if an exception is eligible for route failover (429, empty reply, timeout, 5xx)."""
    if isinstance(exc, EmptyReplyError):
        return True
    if isinstance(exc, (RateLimitError, APITimeoutError, InternalServerError, APIConnectionError)):
        return True
    if isinstance(exc, TimeoutError):
        return True

    status_code = getattr(exc, "status_code", None)
    if status_code == 429 or (status_code is not None and status_code >= 500):
        return True

    msg = str(exc).lower()
    if any(k in msg for k in ("429", "rate limit", "timeout", "empty reply")):
        return True
    for code in ("500", "502", "503", "504"):
        if code in msg:
            return True

    return False


def _backoff_jitter(attempt: int, base: float = 0.05, max_delay: float = 0.5) -> None:
    """Back off with jitter before moving to the next route link."""
    delay = min(max_delay, base * (2 ** min(attempt, 3)))
    jitter = random.uniform(0.01, delay)
    time.sleep(jitter)


def _execute_link_call(
    provider: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
) -> tuple[str, str | None, int]:
    """Execute completion against a single provider link at temperature 0."""
    client = get_client(provider)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    choice = response.choices[0]
    content = choice.message.content or ""
    finish_reason = getattr(choice, "finish_reason", None)

    if not content.strip():
        raise EmptyReplyError(
            f"empty reply (finish_reason={finish_reason}, model={getattr(response, 'model', model)})",
            finish_reason=finish_reason,
        )

    tokens = 0
    if hasattr(response, "usage") and response.usage:
        tokens = getattr(response.usage, "total_tokens", 0) or 0

    return content, finish_reason, tokens


def complete(
    role: str,
    system: str,
    user: str,
    max_tokens: int = 3000,
) -> str:
    """Execute LLM completion with temperature 0, failover across route links, and telemetry."""
    links: list[RouteLink] = get_route_for_role(role)
    errors: list[str] = []

    with _SEMAPHORE:
        for idx, link in enumerate(links):
            t0 = time.time()
            try:
                content, finish_reason, tokens = _execute_link_call(
                    provider=link.provider,
                    model=link.model,
                    system=system,
                    user=user,
                    max_tokens=max_tokens,
                )
                latency = time.time() - t0
                record = CallRecord(
                    role=role,
                    provider=link.provider,
                    model=link.model,
                    tokens=tokens,
                    latency=latency,
                    finish_reason=finish_reason,
                    retries=idx,
                    error=None,
                )
                CALL_LOG.append(record)
                logger.info(
                    "LLM call succeeded role=%s provider=%s model=%s tokens=%s latency=%.3fs finish_reason=%s",
                    role,
                    link.provider,
                    link.model,
                    tokens,
                    latency,
                    finish_reason,
                )
                return content
            except Exception as exc:
                latency = time.time() - t0
                err_msg = str(exc)
                finish_reason = getattr(exc, "finish_reason", None)
                record = CallRecord(
                    role=role,
                    provider=link.provider,
                    model=link.model,
                    tokens=0,
                    latency=latency,
                    finish_reason=finish_reason,
                    retries=idx,
                    error=err_msg,
                )
                CALL_LOG.append(record)
                errors.append(f"{link.provider}:{link.model} -> {err_msg}")
                logger.warning(
                    "LLM call failed role=%s provider=%s model=%s latency=%.3fs error=%s",
                    role,
                    link.provider,
                    link.model,
                    latency,
                    err_msg,
                )

                if _is_failover_error(exc):
                    if idx < len(links) - 1:
                        _backoff_jitter(idx)
                    continue
                raise

        raise AllLinksFailedError(
            f"All links failed for role '{role}'. "
            f"Route: {[f'{l.provider}:{l.model}' for l in links]}. "
            f"Errors: {'; '.join(errors)}"
        )


def complete_json(
    role: str,
    system: str,
    user: str,
    model_cls: type[T],
    max_tokens: int = 3000,
    retries: int = 2,
) -> T:
    """Execute LLM completion expecting JSON, retrying twice with the error fed back."""
    err = ""
    raw = ""
    for _ in range(retries + 1):
        prompt = (
            user
            + (
                f"\n\nYour previous reply was invalid ({err}). Return ONLY valid JSON."
                if err
                else ""
            )
        )
        try:
            raw = complete(role=role, system=system, user=prompt, max_tokens=max_tokens)
            return model_cls.model_validate(_extract_json(raw))
        except (ValueError, Exception) as e:  # noqa: BLE001
            err = f"{str(e)[:200]} | raw_start={raw[:150]!r}"

    raise RuntimeError(f"LLM output failed validation: {err}")


def llm(system: str, user: str, max_tokens: int = 3000, role: str = "extractor") -> str:
    """Prototype-compatible llm completion call."""
    return complete(role=role, system=system, user=user, max_tokens=max_tokens)


def llm_json(
    system: str,
    user: str,
    model_cls: type[T],
    retries: int = 2,
    role: str = "extractor",
    max_tokens: int = 3000,
) -> T:
    """Prototype-compatible llm_json completion call."""
    return complete_json(
        role=role,
        system=system,
        user=user,
        model_cls=model_cls,
        max_tokens=max_tokens,
        retries=retries,
    )
