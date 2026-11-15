"""LLM provider registry, client routing, and resilient completion."""

try:
    from app.llm.client import (
        AllLinksFailedError,
        CallRecord,
        EmptyReplyError,
        LLMError,
        _extract_json,
        clear_call_log,
        complete,
        complete_json,
        get_call_log,
        llm,
        llm_json,
    )
    from app.llm.models import (
        DEFAULT_ROUTES,
        PROVIDERS,
        ProviderConfig,
        RouteLink,
        get_provider_endpoint,
        get_route_for_role,
        parse_route,
        parse_route_link,
    )
except ImportError:
    from backend.app.llm.client import (
        AllLinksFailedError,
        CallRecord,
        EmptyReplyError,
        LLMError,
        _extract_json,
        clear_call_log,
        complete,
        complete_json,
        get_call_log,
        llm,
        llm_json,
    )
    from backend.app.llm.models import (
        DEFAULT_ROUTES,
        PROVIDERS,
        ProviderConfig,
        RouteLink,
        get_provider_endpoint,
        get_route_for_role,
        parse_route,
        parse_route_link,
    )

__all__ = [
    "DEFAULT_ROUTES",
    "PROVIDERS",
    "AllLinksFailedError",
    "CallRecord",
    "EmptyReplyError",
    "LLMError",
    "ProviderConfig",
    "RouteLink",
    "_extract_json",
    "clear_call_log",
    "complete",
    "complete_json",
    "get_call_log",
    "get_provider_endpoint",
    "get_route_for_role",
    "llm",
    "llm_json",
    "parse_route",
    "parse_route_link",
]
