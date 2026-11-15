"""Integration tests for all FastAPI endpoints, caching, PII scrubbing, and replay."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes import _execute_pipeline_task
from backend.app.db.models import (
    LLMCall,
    Review,
    Run,
    RunArtifact,
    RunInput,
    get_session,
    init_db,
)
from backend.app.main import app

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "backend" / "samples"


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure clean isolated database and cleared event buffers for each test."""
    init_db()
    db = get_session()
    try:
        db.query(Review).delete()
        db.query(LLMCall).delete()
        db.query(RunArtifact).delete()
        db.query(RunInput).delete()
        db.query(Run).delete()
        db.commit()
    finally:
        db.close()

    from backend.app.api.routes import _RUN_EVENTS
    _RUN_EVENTS.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def load_sample(filename: str) -> dict:
    with open(SAMPLES_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


# 1. Health and samples endpoints
def test_health_check(client):
    """GET /api/health returns ok status and policy version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["policy_version"] == 1.0


def test_list_samples(client):
    """GET /api/samples returns sample test candidates."""
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 3
    ids = [s["id"] for s in samples]
    assert "A_inflator" in ids
    assert "B_humble" in ids
    assert "C_split" in ids


# 2. Validation tests on POST /api/runs
def test_create_run_validation_size_limit(client):
    """POST /api/runs rejects inputs exceeding maximum characters."""
    payload = {
        "jd": "Job description",
        "resume": "A" * 31000,
        "transcript": "Interviewer: hi\nCandidate: hello",
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400
    assert "exceeds maximum allowed" in response.json()["detail"]


def test_create_run_validation_speaker_labels(client):
    """POST /api/runs rejects transcripts without Interviewer/Candidate labels."""
    payload = {
        "jd": "Senior Engineer",
        "resume": "Built systems",
        "transcript": "Hello this is just an unstructured text.",
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400
    assert "speaker labels" in response.json()["detail"]


# 3. Full run, database PII exclusion, and caching
def test_run_lifecycle_pii_scrubbing_and_caching(client):
    """Verify background execution, zero PII in DB, and zero-call caching on identical submission."""
    sample = load_sample("reject.json")
    # Candidate name Priya Sharma, email priya@example.com, phone +91 98765 43210
    payload = {
        "jd": sample["jd"],
        "resume": sample["resume"],
        "transcript": sample["transcript"],
        "candidate_name": sample["candidate_name"],
    }

    # First submission in mock mode
    response = client.post("/api/runs?mock=true", json=payload)
    assert response.status_code == 202
    data = response.json()
    run_id = data["run_id"]
    assert data["status"] == "PROCESSING"
    assert data["cached"] is False

    # Synchronously execute pipeline task to guarantee DB state is populated
    _execute_pipeline_task(
        run_id=run_id,
        jd=payload["jd"],
        resume=payload["resume"],
        transcript=payload["transcript"],
        candidate_name=payload["candidate_name"],
        mock_mode=True,
    )

    # Verify Database contains NO candidate name, email, or phone
    db = get_session()
    try:
        run_input = db.query(RunInput).filter(RunInput.run_id == run_id).first()
        assert run_input is not None
        assert "[CANDIDATE]" in run_input.resume_redacted
        assert "[EMAIL]" in run_input.resume_redacted
        assert "[PHONE]" in run_input.resume_redacted

        # Explicitly assert raw PII is NOT stored
        assert "priya@example.com" not in run_input.resume_redacted
        assert "98765 43210" not in run_input.resume_redacted
        assert "Priya" not in run_input.resume_redacted
        assert "Sharma" not in run_input.resume_redacted

        # Verify no PII in Run record or artifacts
        run_record = db.query(Run).filter(Run.id == run_id).first()
        assert run_record.status == "COMPLETED"
        assert run_record.decision == "DO_NOT_ADVANCE"
        assert "Priya" not in str(run_record.cache_key)
    finally:
        db.close()

    # GET /api/runs/{id}
    res_get = client.get(f"/api/runs/{run_id}")
    assert res_get.status_code == 200
    run_detail = res_get.json()
    assert run_detail["decision"] == "DO_NOT_ADVANCE"
    assert run_detail["status"] == "COMPLETED"
    assert len(run_detail["llm_calls"]) > 0
    assert "priya@example.com" not in run_detail["inputs"]["resume_redacted"]

    # GET /api/runs
    res_list = client.get("/api/runs")
    assert res_list.status_code == 200
    assert any(r["id"] == run_id for r in res_list.json())

    # Second identical POST makes zero LLM calls and returns cached run
    res_cached = client.post("/api/runs?mock=true", json=payload)
    assert res_cached.status_code == 202
    cached_data = res_cached.json()
    assert cached_data["run_id"] == run_id
    assert cached_data["cached"] is True
    assert cached_data["decision"] == "DO_NOT_ADVANCE"


# 4. SSE Events endpoint
def test_stream_events_endpoint(client):
    """GET /api/runs/{run_id}/events streams SSE progress events."""
    sample = load_sample("hire.json")
    payload = {
        "jd": sample["jd"],
        "resume": sample["resume"],
        "transcript": sample["transcript"],
        "candidate_name": "",
    }
    res = client.post("/api/runs?mock=true", json=payload)
    run_id = res.json()["run_id"]

    # Execute pipeline
    _execute_pipeline_task(
        run_id=run_id,
        jd=payload["jd"],
        resume=payload["resume"],
        transcript=payload["transcript"],
        candidate_name="",
        mock_mode=True,
    )

    # Stream events
    res_stream = client.get(f"/api/runs/{run_id}/events")
    assert res_stream.status_code == 200
    assert "text/event-stream" in res_stream.headers["content-type"]
    text = res_stream.text
    assert "event:" in text
    assert "done" in text


# 5. Replay endpoint produces identical results
def test_replay_is_identical(client):
    """POST /api/runs/{run_id}/replay yields identical decisions and empty diff."""
    sample = load_sample("review.json")
    payload = {
        "jd": sample["jd"],
        "resume": sample["resume"],
        "transcript": sample["transcript"],
        "candidate_name": "",
    }
    res = client.post("/api/runs?mock=true", json=payload)
    run_id = res.json()["run_id"]

    _execute_pipeline_task(
        run_id=run_id,
        jd=payload["jd"],
        resume=payload["resume"],
        transcript=payload["transcript"],
        candidate_name="",
        mock_mode=True,
    )

    res_replay = client.post(f"/api/runs/{run_id}/replay")
    assert res_replay.status_code == 200
    replay_data = res_replay.json()
    assert replay_data["identical"] is True
    assert replay_data["diff"] == {}
    assert replay_data["original"]["decision"] == "REVIEW"
    assert replay_data["replay"]["decision"] == "REVIEW"


# 6. Human review endpoint
def test_create_review_endpoint(client):
    """POST /api/runs/{run_id}/review stores human confirmation decision."""
    sample = load_sample("review.json")
    payload = {
        "jd": sample["jd"],
        "resume": sample["resume"],
        "transcript": sample["transcript"],
        "candidate_name": "",
    }
    res = client.post("/api/runs?mock=true", json=payload)
    run_id = res.json()["run_id"]

    _execute_pipeline_task(
        run_id=run_id,
        jd=payload["jd"],
        resume=payload["resume"],
        transcript=payload["transcript"],
        candidate_name="",
        mock_mode=True,
    )

    rev_payload = {
        "decision": "DO_NOT_ADVANCE",
        "reviewer": "Auditor Dave",
        "notes": "Candidate was dismissive of code reviews; reject confirmed.",
    }
    res_rev = client.post(f"/api/runs/{run_id}/review", json=rev_payload)
    assert res_rev.status_code == 201
    assert res_rev.json()["decision"] == "DO_NOT_ADVANCE"
    assert res_rev.json()["reviewer"] == "Auditor Dave"

    # Confirm review is reflected in run details
    run_details = client.get(f"/api/runs/{run_id}").json()
    assert len(run_details["reviews"]) == 1
    assert run_details["reviews"][0]["decision"] == "DO_NOT_ADVANCE"
