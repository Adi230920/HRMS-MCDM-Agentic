# trd.md

Stack:
- Backend: Python 3.11, FastAPI, Pydantic v2, LangGraph.
- Frontend: Next.js App Router, TypeScript, Tailwind.
- Database: SQLite through SQLAlchemy.
- LLM: OpenAI-compatible client, free tiers only.

Environment variables: see .env.example.
Config: policy.yaml holds thresholds; .env holds keys and model routes.
Caching: hash redacted input plus policy version plus model routes; return the stored run on a match.

Endpoints:
- POST /api/runs returns 202 and run_id.
- GET /api/runs/{id}/events streams progress over SSE.
- GET /api/runs/{id} and GET /api/runs return results.
- POST /api/runs/{id}/replay reruns conflicts and gate on stored outputs.
- POST /api/runs/{id}/review stores the human decision.
- GET /api/samples and GET /api/health.

Tables: runs, run_inputs (redacted only), run_artifacts, llm_calls, reviews.
