"""LLM provider registry and role routing configuration."""

import os
from dataclasses import dataclass
from typing import NamedTuple

try:
    from backend.app.config import settings
except ImportError:
    from app.config import settings


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    base_url_var: str
    api_key_var: str
    default_base_url: str


PROVIDERS: dict[str, ProviderConfig] = {
    "groq": ProviderConfig(
        name="groq",
        base_url_var="GROQ_BASE_URL",
        api_key_var="GROQ_API_KEY",
        default_base_url="https://api.groq.com/openai/v1",
    ),
    "gemini": ProviderConfig(
        name="gemini",
        base_url_var="GEMINI_BASE_URL",
        api_key_var="GEMINI_API_KEY",
        default_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    ),
    "openrouter": ProviderConfig(
        name="openrouter",
        base_url_var="OPENROUTER_BASE_URL",
        api_key_var="OPENROUTER_API_KEY",
        default_base_url="https://openrouter.ai/api/v1",
    ),
}


class RouteLink(NamedTuple):
    """A single link in a model route chain (provider and model name)."""

    provider: str
    model: str


DEFAULT_ROUTES: dict[str, str] = {
    "extractor": "groq:qwen/qwen3.8-27b,gemini:gemini-3.5-flash-lite,openrouter:openrouter/free",
    "technical": (
        "gemini:gemini-3.5-flash-lite,groq:openai/gpt-oss-120b,"
        "openrouter:google/gemma-4-31b-it:free"
    ),
    "manager": (
        "groq:openai/gpt-oss-120b,openrouter:openrouter/free,"
        "gemini:gemini-3.5-flash-lite"
    ),
    "hr": (
        "openrouter:openrouter/free,gemini:gemini-3.5-flash-lite,"
        "groq:qwen/qwen3.8-27b"
    ),
    "moderator": "gemini:gemini-3.5-flash-lite,groq:openai/gpt-oss-120b,openrouter:openrouter/free",
    "chair": "groq:openai/gpt-oss-120b,gemini:gemini-3.5-flash-lite,openrouter:openrouter/free",
}


def parse_route_link(entry: str) -> RouteLink:
    """Parse a single provider:model entry, splitting on the first colon only."""
    entry = entry.strip()
    if not entry:
        raise ValueError("Route entry cannot be empty")
    parts = entry.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid route entry '{entry}'. Expected format 'provider:model'")
    provider = parts[0].strip().lower()
    model = parts[1].strip()
    if not provider or not model:
        raise ValueError(f"Invalid route entry '{entry}'. Both provider and model must be specified")
    return RouteLink(provider=provider, model=model)


def parse_route(route_str: str) -> list[RouteLink]:
    """Parse a comma-separated route chain, splitting each entry on the first colon only."""
    links: list[RouteLink] = []
    for item in route_str.split(","):
        cleaned = item.strip()
        if cleaned:
            links.append(parse_route_link(cleaned))
    if not links:
        raise ValueError(f"No valid route links found in '{route_str}'")
    return links


ROLE_ALIASES: dict[str, str] = {
    "delivery": "manager",
    "collaboration": "hr",
}


def get_route_for_role(role: str) -> list[RouteLink]:
    """Get the ordered route chain for a role, honoring ROUTE_* overrides and aliases."""
    role_key = role.strip().lower()
    role_canonical = ROLE_ALIASES.get(role_key, role_key)

    env_var = f"ROUTE_{role_key.upper()}"
    env_var_canonical = f"ROUTE_{role_canonical.upper()}"

    route_override = os.environ.get(env_var) or os.environ.get(env_var_canonical)
    if not route_override and hasattr(settings, env_var):
        val = getattr(settings, env_var)
        if val:
            route_override = val
    if not route_override and hasattr(settings, env_var_canonical):
        val = getattr(settings, env_var_canonical)
        if val:
            route_override = val

    raw_route = route_override or DEFAULT_ROUTES.get(role_canonical) or DEFAULT_ROUTES.get(role_key)
    if not raw_route:
        expected = list(DEFAULT_ROUTES.keys()) + list(ROLE_ALIASES.keys())
        raise ValueError(f"Unknown role '{role}'. Expected one of {expected}")

    return parse_route(raw_route)


def get_provider_endpoint(provider: str) -> tuple[str, str]:
    """Return (base_url, api_key) for a registered provider."""
    p = PROVIDERS.get(provider.lower())
    if not p:
        raise ValueError(
            f"Unknown provider '{provider}'. Registered providers: {list(PROVIDERS.keys())}"
        )

    base_url = (
        os.environ.get(p.base_url_var)
        or getattr(settings, p.base_url_var, p.default_base_url)
        or p.default_base_url
    )
    api_key = os.environ.get(p.api_key_var) or getattr(settings, p.api_key_var, "") or ""
    return base_url, api_key
