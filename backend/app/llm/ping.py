"""Ping configured LLM providers with a minimal test prompt."""

import sys
import time
from pathlib import Path

# Ensure backend root is on sys.path if run directly as script or module
backend_root = Path(__file__).resolve().parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from openai import OpenAI

try:
    from backend.app.llm.models import PROVIDERS, get_provider_endpoint
except ImportError:
    from app.llm.models import PROVIDERS, get_provider_endpoint

DEFAULT_MODELS: dict[str, str] = {
    "groq": "openai/gpt-oss-120b",
    "gemini": "gemini-3.5-flash-lite",
    "openrouter": "openrouter/free",
}


def ping_provider(provider: str) -> dict:
    """Send one tiny prompt to a provider if configured."""
    base_url, api_key = get_provider_endpoint(provider)
    if not api_key:
        return {
            "provider": provider,
            "status": "SKIPPED",
            "reason": f"No API key configured in {PROVIDERS[provider].api_key_var}",
        }

    model = DEFAULT_MODELS.get(provider, "gpt-3.5-turbo")
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=15.0)

    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=80,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a health check."},
                {"role": "user", "content": "Ping"},
            ],
        )
        latency = time.time() - t0
        choice = response.choices[0]
        content = choice.message.content or ""
        if not content and getattr(choice.message, "reasoning", None):
            content = f"[reasoning] {choice.message.reasoning[:40]}..."
        return {
            "provider": provider,
            "status": "OK",
            "model": model,
            "latency": latency,
            "reply": content.strip()[:60],
        }
    except Exception as exc:  # noqa: BLE001
        latency = time.time() - t0
        return {
            "provider": provider,
            "status": "FAILED",
            "model": model,
            "latency": latency,
            "error": str(exc),
        }


def ping_all() -> dict[str, dict]:
    """Ping all configured providers in registry."""
    print("Pinging configured LLM providers...")
    results = {}
    for provider in PROVIDERS:
        res = ping_provider(provider)
        results[provider] = res
        status = res["status"]
        if status == "OK":
            print(
                f"[{provider}] OK (model={res['model']}, latency={res['latency']:.2f}s, "
                f"reply={res['reply']!r})"
            )
        elif status == "SKIPPED":
            print(f"[{provider}] SKIPPED: {res['reason']}")
        else:
            print(
                f"[{provider}] FAILED (model={res['model']}, latency={res['latency']:.2f}s): "
                f"{res['error']}"
            )
    return results


if __name__ == "__main__":
    ping_all()
