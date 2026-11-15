# build_order.md

One milestone per prompt. Each prompt names the prep files to read first. Keep diffs small. Do not start the next until tests pass.

- M0: repo, folders, policy.yaml, .env.example.
- M1: core/ with unit tests, no network.
- M2: llm/models.py and llm/client.py, tested with a fake provider.
- M3: agents, extractor, moderator, and chair, tested with recorded outputs.
- M4: LangGraph pipeline; a CLI runs the three samples.
- M5: API, SQLite, SSE, cache by input hash, replay.
- M6: frontend screens.
- M7: evaluation with ten labelled cases and a single-LLM baseline.

Done: three samples match expected decisions through the UI, replay is identical, and no raw PII is stored.
