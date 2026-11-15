# llm_providers.md

Free tiers only. Spread calls across three providers to stay under rate limits: Groq, Gemini AI Studio, OpenRouter free models. All are OpenAI-compatible.

llm/models.py holds provider settings and, per role, an ordered chain of provider and model pairs. Defaults live there; ROUTE_* variables in .env override them.

llm/client.py rules:
- Temperature 0, max_tokens 3000.
- Retry twice on invalid JSON, feeding the error back.
- On 429, empty reply, or timeout, back off with jitter, then try the next link.
- One call at a time.
- Log the model actually used, tokens, latency, and finish reason.

Use non-reasoning models only. Confirm model names in each catalogue before pinning them.
