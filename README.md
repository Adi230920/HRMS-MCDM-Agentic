# HRMS-MCDM-Agentic

TalentCouncil is an AI-assisted hiring decision support system that cross-examines candidate resume claims against interview transcripts using multi-agent deliberation, deterministic policy gates, and audit trails.

---

## 1. Setup

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ and `npm`

### Backend Installation
From the repository root:
```bash
# Optional: create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install Python dependencies in editable mode
pip install -e .
```

### Frontend Installation
```bash
cd frontend
npm install
cd ..
```

---

## 2. Environment Variables and Keys

Copy `.env.example` to `.env` in the repository root:
```bash
cp .env.example .env
```

### Configuration Options
| Variable | Description | Default / Example |
|---|---|---|
| `GROQ_API_KEY` | API key for Groq models (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`) | `gsk_...` |
| `GEMINI_API_KEY` | API key for Google Gemini (`gemini-3.5-flash-lite`) | `AIzaSy...` |
| `OPENROUTER_API_KEY` | API key for OpenRouter free models (`openrouter/free`, `google/gemma-4-31b-it:free`) | `sk-or-...` |
| `DATABASE_URL` | SQLite database file location | `sqlite:///./talentcouncil.db` |
| `FRONTEND_ORIGIN` | Allowed CORS origin for Next.js frontend | `http://localhost:3000` |
| `MOCK_LLM` | Global toggle for mock replay mode | `false` |

> [!IMPORTANT]
> **Synthetic Data & Privacy**: Free tier model providers may retain prompt data. Never submit raw candidate names, resumes, transcripts, or personal data. All PII is scrubbed before LLM dispatch.

---

## 3. Running Backend and Frontend

### Run Backend API
Start the FastAPI server on port 8000:
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

### Run Frontend UI
Start the Next.js development server:
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Run via CLI
Execute individual candidate evaluations directly from the command line:
```bash
python -m backend.app.cli run prep/samples/hire.json --mock
```

---

## 4. Mock versus Live Mode

### Mock Mode
- **Zero API Keys Required**: Uses deterministic recorded fixtures with verbatim quote evidence.
- **Activation**:
  - In `.env`: Set `MOCK_LLM=true`
  - Via API: Pass `?mock=true` query parameter to `POST /api/runs`
  - Via CLI: Pass `--mock` flag to `python -m backend.app.cli run <sample_path>`
- **Fixtures**: Stored in `backend/tests/fixtures/samples.py` for `hire` (`B_humble`), `reject` (`A_inflator`), and `review` (`C_split`).

### Live Mode
- **Multi-Provider Routing**: Calls live LLMs across Groq, Gemini, and OpenRouter per `backend/policy.yaml`.
- **Activation**:
  - Set `MOCK_LLM=false` in `.env`
  - Provide valid API keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`)
  - Redaction, claim extraction, and deterministic policy gates still run purely in local Python code.

---

## 5. Verification and Testing

### Unit and Integration Tests
Run the complete automated pytest suite (60 tests):
```bash
pytest
```

### End-to-End Demo Verification Script
Run the end-to-end evaluation script across all three canonical samples:
```bash
python scripts/verify_demo.py
```
This script submits the 3 samples (`hire.json`, `reject.json`, `review.json`), polls for completion, and asserts all PRD success criteria:
- Expected decision match for 3 of 3 samples
- Run duration under 120 seconds
- At most 7 LLM calls per evaluation
- Deterministic identical replay on stored outputs (`POST /api/runs/{id}/replay`)
- Zero unredacted PII stored in SQLite database

