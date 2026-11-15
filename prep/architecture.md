# architecture.md

Pipeline, in order:
- redact (code)
- parse transcript (code)
- extract claims (LLM, extractor)
- three agents evaluate (LLM: technical_evaluator, manager, hr_agent)
- verify quotes, derive recommendations (code)
- detect conflicts (code)
- debate, one batched call, skipped if no conflicts (LLM, moderator)
- gate decides (code)
- chair writes summary (LLM)
- persist and stream events

LLM calls per run: five or six.

Each node takes and returns Pydantic objects. Nodes share no hidden state.

An LLM failure degrades the run; it never crashes it. Conflict and gate rules run in code only. Details: conflict_rules.md, gate_logic.md.

Replay: rerun conflicts and gate on stored agent outputs. The result must match exactly.
