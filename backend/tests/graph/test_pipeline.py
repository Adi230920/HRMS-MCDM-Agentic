"""Tests for the LangGraph hiring council pipeline, replay fixtures, and CLI."""

import json
from pathlib import Path

import pytest

from backend.app.cli import cmd_run
from backend.app.graph.pipeline import run_council
from backend.tests.fixtures.samples import MockReplayLLMClient

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "backend" / "samples"


def load_sample(filename: str) -> dict:
    with open(SAMPLES_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def test_mock_pipeline_reject_gives_do_not_advance():
    """Mock pipeline on reject sample yields DO_NOT_ADVANCE with veto signals."""
    sample = load_sample("reject.json")
    client = MockReplayLLMClient("reject")

    res = run_council(
        jd=sample["jd"],
        resume=sample["resume"],
        transcript=sample["transcript"],
        candidate_name=sample.get("candidate_name", ""),
        llm_client=client,
    )

    assert res["decision"] == "DO_NOT_ADVANCE"
    assert res["veto"] is True
    assert "contradicted_claim" in res["veto_signals"]
    assert res["initial"]["TECHNICAL"] == "DO_NOT_ADVANCE"
    assert res["initial"]["DELIVERY"] == "DO_NOT_ADVANCE"
    assert res["final"]["TECHNICAL"] == "DO_NOT_ADVANCE"
    assert res["llm_calls"] > 0
    assert len(res["trace"]) > 0
    assert len(res["chair"]) > 0


def test_mock_pipeline_hire_gives_advance():
    """Mock pipeline on hire sample yields ADVANCE and skips debate node."""
    sample = load_sample("hire.json")
    client = MockReplayLLMClient("hire")

    res = run_council(
        jd=sample["jd"],
        resume=sample["resume"],
        transcript=sample["transcript"],
        candidate_name=sample.get("candidate_name", ""),
        llm_client=client,
    )

    assert res["decision"] == "ADVANCE"
    assert res["council_score"] == 1.0
    assert res["quorum"] is True
    assert res["veto"] is False
    assert res["argued"] is False  # Debate skipped because no conflict points
    assert len(res["points"]) == 0
    assert not any(stage == "debate" for stage, _ in res["trace"])


def test_mock_pipeline_review_gives_review():
    """Mock pipeline on review sample yields REVIEW due to directional split."""
    sample = load_sample("review.json")
    client = MockReplayLLMClient("review")

    res = run_council(
        jd=sample["jd"],
        resume=sample["resume"],
        transcript=sample["transcript"],
        candidate_name=sample.get("candidate_name", ""),
        llm_client=client,
    )

    assert res["decision"] == "REVIEW"
    assert res["argued"] is True
    assert len(res["points"]) > 0
    assert any(p.rule == "directional_split" for p in res["points"])
    assert "alone against council" in res["outliers"].get("COLLABORATION", [])


def test_pipeline_failed_agent_recorded_and_continues(monkeypatch):
    """When one agent fails, error is recorded in failed map and run completes."""
    sample = load_sample("hire.json")
    client = MockReplayLLMClient("hire")

    # Force technical evaluator to fail
    def failing_eval(*args, **kwargs):
        raise RuntimeError("Technical agent network timeout")

    monkeypatch.setattr("backend.app.agents.technical_evaluator.run", failing_eval)

    res = run_council(
        jd=sample["jd"],
        resume=sample["resume"],
        transcript=sample["transcript"],
        candidate_name=sample.get("candidate_name", ""),
        llm_client=client,
    )

    assert "TECHNICAL" in res["failed"]
    assert "Technical agent network timeout" in res["failed"]["TECHNICAL"]
    assert "DELIVERY" in res["evals"]
    assert "COLLABORATION" in res["evals"]
    assert "decision" in res


def test_pipeline_all_agents_failing_fails_run(monkeypatch):
    """When all agents fail, pipeline raises RuntimeError."""
    sample = load_sample("hire.json")
    client = MockReplayLLMClient("hire")

    def failing_eval(*args, **kwargs):
        raise RuntimeError("Agent failure")

    monkeypatch.setattr("backend.app.agents.technical_evaluator.run", failing_eval)
    monkeypatch.setattr("backend.app.agents.manager.run", failing_eval)
    monkeypatch.setattr("backend.app.agents.hr_agent.run", failing_eval)

    with pytest.raises(RuntimeError, match="All agents failed"):
        run_council(
            jd=sample["jd"],
            resume=sample["resume"],
            transcript=sample["transcript"],
            candidate_name=sample.get("candidate_name", ""),
            llm_client=client,
        )


def test_pipeline_event_callback():
    """Event callback receives milestone notifications during pipeline run."""
    sample = load_sample("hire.json")
    client = MockReplayLLMClient("hire")
    events = []

    def callback(name, data):
        events.append((name, data))

    res = run_council(
        jd=sample["jd"],
        resume=sample["resume"],
        transcript=sample["transcript"],
        candidate_name=sample.get("candidate_name", ""),
        event_callback=callback,
        llm_client=client,
    )

    event_names = [e[0] for e in events]
    assert "ingest_completed" in event_names
    assert "agent_completed" in event_names
    assert "conflicts_detected" in event_names
    assert "gate_completed" in event_names
    assert "chair_completed" in event_names
    assert res["decision"] == "ADVANCE"


def test_cli_mock_execution(capsys):
    """CLI runs sample with --mock flag and prints prototype show() summary."""
    class Args:
        sample_path = "samples/review.json"
        mock = True

    cmd_run(Args())
    captured = capsys.readouterr().out
    assert "DECISION: REVIEW" in captured
    assert "council_score=" in captured
    assert "debate_argued=True" in captured
