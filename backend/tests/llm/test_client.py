"""Unit tests for the LLM layer: routes, fallbacks, retries, and telemetry."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from backend.app.llm.client import (
    AllLinksFailedError,
    EmptyReplyError,
    _extract_json,
    clear_call_log,
    complete,
    complete_json,
    get_call_log,
    llm,
    llm_json,
)
from backend.app.llm.models import (
    RouteLink,
    get_route_for_role,
    parse_route,
    parse_route_link,
)
from backend.app.llm.ping import ping_provider


class CandidateEval(BaseModel):
    decision: str
    score: int


@pytest.fixture(autouse=True)
def _reset_telemetry(monkeypatch):
    """Clear call logs and disable backoff sleeps for instant testing."""
    clear_call_log()
    monkeypatch.setattr("backend.app.llm.client._backoff_jitter", lambda attempt: None)


# 1. Route parsing test including :free slug
def test_route_containing_free_slug_parses_correctly():
    """Verify route strings containing colons in model names (e.g. :free) parse on first colon only."""
    entry = "openrouter:meta-llama/llama-3.3-70b-instruct:free"
    link = parse_route_link(entry)
    assert link.provider == "openrouter"
    assert link.model == "meta-llama/llama-3.3-70b-instruct:free"

    full_chain = (
        "gemini:gemini-2.5-flash,"
        "groq:llama-3.3-70b-versatile,"
        "openrouter:meta-llama/llama-3.3-70b-instruct:free"
    )
    links = parse_route(full_chain)
    assert len(links) == 3
    assert links[2] == RouteLink(
        provider="openrouter",
        model="meta-llama/llama-3.3-70b-instruct:free",
    )

    # Check default technical route has :free slug intact
    tech_route = get_route_for_role("technical")
    free_links = [l for l in tech_route if ":free" in l.model]
    assert len(free_links) == 1
    assert free_links[0].provider == "openrouter"


def test_route_env_override(monkeypatch):
    """Verify ROUTE_* environment variable overrides default role routes."""
    override = "openrouter:test-model:free,groq:llama-3"
    monkeypatch.setenv("ROUTE_CHAIR", override)
    route = get_route_for_role("chair")
    assert len(route) == 2
    assert route[0] == RouteLink(provider="openrouter", model="test-model:free")
    assert route[1] == RouteLink(provider="groq", model="llama-3")


# 2. 429 rate limit fallthrough test
def test_429_falls_through_to_the_next_link(monkeypatch):
    """A 429 rate limit on the first link must fall through to the next link."""
    # moderator route: gemini:gemini-2.5-flash, groq:llama-3.3-70b-versatile
    calls = []

    def mock_execute(provider, model, system, user, max_tokens):
        calls.append((provider, model))
        if provider == "gemini":
            from openai import RateLimitError
            response_mock = MagicMock()
            response_mock.status_code = 429
            raise RateLimitError("Rate limit exceeded (429)", response=response_mock, body=None)
        return "Success from groq", "stop", 50

    monkeypatch.setattr("backend.app.llm.client._execute_link_call", mock_execute)

    result = complete("moderator", system="System prompt", user="User question")
    assert result == "Success from groq"
    assert len(calls) == 2
    assert calls[0][0] == "gemini"
    assert calls[1][0] == "groq"

    # Verify telemetry records both attempts
    log = get_call_log()
    assert len(log) == 2
    assert log[0].provider == "gemini"
    assert log[0].error is not None
    assert "429" in log[0].error
    assert log[1].provider == "groq"
    assert log[1].error is None
    assert log[1].tokens == 50
    assert log[1].finish_reason == "stop"


# 3. Empty reply with finish_reason=length fallthrough test
def test_empty_reply_with_finish_reason_length_falls_through(monkeypatch):
    """An empty reply with finish_reason='length' must trigger fallthrough to the next link."""
    calls = []

    def mock_execute(provider, model, system, user, max_tokens):
        calls.append((provider, model))
        if len(calls) == 1:
            raise EmptyReplyError(
                f"empty reply (finish_reason=length, model={model})",
                finish_reason="length",
            )
        return "Recovered content from second provider", "stop", 35

    monkeypatch.setattr("backend.app.llm.client._execute_link_call", mock_execute)

    result = complete("extractor", system="sys", user="user")
    assert result == "Recovered content from second provider"
    assert len(calls) == 2

    log = get_call_log()
    assert len(log) == 2
    assert log[0].finish_reason == "length"
    assert log[0].error is not None
    assert "empty reply" in log[0].error
    assert log[1].error is None
    assert log[1].finish_reason == "stop"


# 4. Bad JSON then good JSON test
def test_bad_json_then_good_json_succeeds(monkeypatch):
    """Bad JSON on first attempt is corrected on retry when error is fed back."""
    prompts_received = []

    def mock_complete(role, system, user, max_tokens=3000):
        prompts_received.append(user)
        if len(prompts_received) == 1:
            # First attempt returns conversational text with broken JSON
            return "Sure! Here is the JSON: { 'decision': 'ADVANCE' missing closing"
        # Second attempt returns valid JSON
        return '{"decision": "ADVANCE", "score": 90}'

    monkeypatch.setattr("backend.app.llm.client.complete", mock_complete)

    parsed = complete_json("extractor", system="sys", user="Evaluate candidate", model_cls=CandidateEval)
    assert parsed.decision == "ADVANCE"
    assert parsed.score == 90
    assert len(prompts_received) == 2
    assert "Your previous reply was invalid" in prompts_received[1]


def test_invalid_json_exhausts_retries_and_raises(monkeypatch):
    """If model continuously returns invalid JSON, RuntimeError is raised after 2 retries."""
    monkeypatch.setattr(
        "backend.app.llm.client.complete",
        lambda role, system, user, max_tokens=3000: "Not JSON at all",
    )

    with pytest.raises(RuntimeError, match="LLM output failed validation"):
        complete_json("extractor", system="sys", user="Eval", model_cls=CandidateEval, retries=2)


# 5. All links failing raises clear error
def test_all_links_failing_raises(monkeypatch):
    """When every link in a route chain fails, AllLinksFailedError is raised with clear details."""
    def mock_execute(provider, model, system, user, max_tokens):
        from openai import RateLimitError
        response_mock = MagicMock()
        response_mock.status_code = 429
        raise RateLimitError("Rate limit 429", response=response_mock, body=None)

    monkeypatch.setattr("backend.app.llm.client._execute_link_call", mock_execute)

    with pytest.raises(AllLinksFailedError) as exc_info:
        complete("extractor", system="sys", user="user")

    err_text = str(exc_info.value)
    assert "All links failed for role 'extractor'" in err_text
    assert "groq" in err_text
    assert "gemini" in err_text


# 6. JSON extraction robust parsing
def test_extract_json_boundaries():
    """Verify _extract_json ignores chat prefix and suffix around outermost curly braces."""
    raw = "Hello! Here is the result:\n```json\n{\"decision\": \"REVIEW\", \"score\": 75}\n```\nHope that helps!"
    extracted = _extract_json(raw)
    assert extracted == {"decision": "REVIEW", "score": 75}

    with pytest.raises(ValueError, match="no JSON object in reply"):
        _extract_json("No braces here")


# 7. Ping CLI utility test
def test_ping_provider_no_key(monkeypatch):
    """Ping utility skips providers without an API key."""
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setattr("backend.app.config.settings.GROQ_API_KEY", "")
    res = ping_provider("groq")
    assert res["status"] == "SKIPPED"
    assert "No API key configured" in res["reason"]


def test_ping_provider_success(monkeypatch):
    """Ping utility succeeds with mock client."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk-mock-key")
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Pong"
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response

    monkeypatch.setattr("backend.app.llm.ping.OpenAI", lambda **kwargs: mock_client)
    res = ping_provider("groq")
    assert res["status"] == "OK"
    assert res["reply"] == "Pong"


# 8. Prototype compatibility helpers
def test_prototype_compatibility_wrappers(monkeypatch):
    """Verify llm() and llm_json() drop-in compatibility functions work."""
    monkeypatch.setattr(
        "backend.app.llm.client.complete",
        lambda role, system, user, max_tokens=3000: '{"decision": "ADVANCE", "score": 100}',
    )
    raw = llm("sys", "user")
    assert "ADVANCE" in raw

    parsed = llm_json("sys", "user", CandidateEval)
    assert parsed.decision == "ADVANCE"
    assert parsed.score == 100
