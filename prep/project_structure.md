# project_structure.md

backend/app/
- core/: redact.py, parse.py, quotes.py, scoring.py, rules.py, gate.py, schemas.py, policy.py. Pure Python.
- llm/models.py: provider registry and role routes. Only file containing model names.
- llm/client.py: calls, retries, fallback, rate limiting.
- agents/: base.py, technical_evaluator.py, manager.py, hr_agent.py, chair.py, extractor.py, moderator.py. One file per agent.
- graph/pipeline.py: LangGraph wiring.
- api/routes.py, db/models.py, main.py.

Also:
- backend/policy.yaml, backend/samples/, backend/tests/
- frontend/ with app, components, lib
- prep/ holds these specs

Naming: snake_case files. Each agent file exports one run function taking a Dossier and returning an AgentEval.
Tests: tests/core, tests/agents, tests/api, and tests/fixtures holding recorded LLM outputs.
Rule: core/ never imports from llm, agents, db, or api. Keep modules under 200 lines.
