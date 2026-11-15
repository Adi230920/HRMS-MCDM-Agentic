"""Unit tests for evaluation agents, extractor, moderator, and chair."""

from typing import Any

from backend.app.agents import (
    chair,
    extractor,
    hr_agent,
    manager,
    moderator,
    technical_evaluator,
)
from backend.app.core.rules import Point
from backend.app.core.schemas import (
    AgentEval,
    Claim,
    CriterionRating,
    Dossier,
    Turn,
)


class FakeLLMClient:
    """Mock LLM client returning canned JSON or text without network calls."""

    def __init__(
        self,
        json_response: Any = None,
        text_response: str | None = None,
        should_fail: bool = False,
    ) -> None:
        self.json_response = json_response
        self.text_response = text_response
        self.should_fail = should_fail
        self.calls: list[dict[str, Any]] = []

    def complete_json(
        self,
        role: str,
        system: str,
        user: str,
        model_cls: type,
        **kwargs: Any,
    ) -> Any:
        self.calls.append({"role": role, "system": system, "user": user})
        if self.should_fail:
            raise RuntimeError("Fake LLM provider failure")
        data = self.json_response(role, user) if callable(self.json_response) else self.json_response
        return model_cls.model_validate(data)

    def complete(
        self,
        role: str,
        system: str,
        user: str,
        max_tokens: int = 3000,
    ) -> str:
        self.calls.append({"role": role, "system": system, "user": user, "max_tokens": max_tokens})
        if self.should_fail:
            raise RuntimeError("Fake network failure")
        return self.text_response or ""


def create_sample_dossier() -> Dossier:
    """Create a minimal valid Dossier for testing."""
    return Dossier(
        jd="Senior AI Engineer: build RAG systems and deploy on Kubernetes.",
        resume="Software Engineer. Built RAG systems using FAISS vector search.",
        turns=[
            Turn(
                id="T1",
                speaker="INTERVIEWER",
                text="Tell me how you built the vector search.",
            ),
            Turn(
                id="T2",
                speaker="CANDIDATE",
                text="I tuned HNSW index parameters in FAISS to improve query recall.",
            ),
        ],
        claims=[
            Claim(
                id="C1",
                text="Built RAG systems using FAISS",
                category="technical",
                resume_quote="Built RAG systems using FAISS vector search.",
            )
        ],
    )


# 1. Schema validation
def test_schema_validation():
    """Valid canned JSON is properly parsed into an AgentEval model."""
    dossier = create_sample_dossier()
    canned = {
        "ratings": [
            {
                "criterion": "core_technical_depth",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I tuned HNSW index parameters in FAISS to improve query recall.",
                    }
                ],
            },
            {"criterion": "system_design_reasoning", "rating": "PARTIAL", "evidence": []},
            {"criterion": "problem_solving_clarity", "rating": "PARTIAL", "evidence": []},
            {"criterion": "claim_vs_transcript_proof", "rating": "PARTIAL", "evidence": []},
        ],
        "claim_findings": [
            {
                "claim_id": "C1",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I tuned HNSW index parameters in FAISS to improve query recall.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Candidate knows FAISS well",
        "reasoning": "Strong technical depth demonstrated in transcript.",
    }
    client = FakeLLMClient(json_response=canned)
    result = technical_evaluator.run(dossier, client)

    assert isinstance(result, AgentEval)
    assert result.agent == "TECHNICAL"
    assert len(result.ratings) == 4
    assert result.ratings[0].criterion == "core_technical_depth"
    assert result.ratings[0].rating == "STRONG"


# 2. Exact rubric forced
def test_exact_rubric_forced():
    """Rubric forces exact criterion IDs: drops unknown ones and populates missing ones as NOT_DEMONSTRATED."""
    dossier = create_sample_dossier()
    # LLM returns an invented criterion and misses 2 required criteria
    canned = {
        "ratings": [
            {"criterion": "core_technical_depth", "rating": "PARTIAL", "evidence": []},
            {"criterion": "system_design_reasoning", "rating": "STRONG", "evidence": []},
            {"criterion": "invented_extra_criterion", "rating": "STRONG", "evidence": []},
        ],
        "claim_findings": [],
        "recommendation": "REVIEW",
        "whisper": "Test",
        "reasoning": "Test",
    }
    client = FakeLLMClient(json_response=canned)
    result = technical_evaluator.run(dossier, client)

    expected_criteria = [
        "core_technical_depth",
        "system_design_reasoning",
        "problem_solving_clarity",
        "claim_vs_transcript_proof",
    ]
    actual_criteria = [r.criterion for r in result.ratings]
    assert actual_criteria == expected_criteria

    # Missing criteria default to NOT_DEMONSTRATED
    rating_map = {r.criterion: r.rating for r in result.ratings}
    assert rating_map["problem_solving_clarity"] == "NOT_DEMONSTRATED"
    assert rating_map["claim_vs_transcript_proof"] == "NOT_DEMONSTRATED"
    assert "invented_extra_criterion" not in rating_map


# 3. Bad claim IDs dropped
def test_bad_claim_ids_dropped():
    """Claim findings referencing non-existent claim IDs are dropped."""
    dossier = create_sample_dossier()  # contains only C1
    canned = {
        "ratings": [
            {"criterion": "core_technical_depth", "rating": "PARTIAL", "evidence": []},
            {"criterion": "system_design_reasoning", "rating": "PARTIAL", "evidence": []},
            {"criterion": "problem_solving_clarity", "rating": "PARTIAL", "evidence": []},
            {"criterion": "claim_vs_transcript_proof", "rating": "PARTIAL", "evidence": []},
        ],
        "claim_findings": [
            {"claim_id": "C1", "status": "SUPPORTED", "evidence": []},
            {"claim_id": "C99_HALLUCINATED", "status": "CONTRADICTED", "evidence": []},
        ],
        "recommendation": "REVIEW",
        "whisper": "Test",
        "reasoning": "Test",
    }
    client = FakeLLMClient(json_response=canned)
    result = technical_evaluator.run(dossier, client)

    claim_ids = [f.claim_id for f in result.claim_findings]
    assert claim_ids == ["C1"]


# 4. Downgrade applied
def test_downgrade_applied():
    """STRONG rating without verified candidate transcript quote is downgraded."""
    dossier = create_sample_dossier()
    # Quote does not exist in candidate transcript
    canned = {
        "ratings": [
            {
                "criterion": "core_technical_depth",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Invented quote that candidate never said.",
                    }
                ],
            },
            {"criterion": "system_design_reasoning", "rating": "PARTIAL", "evidence": []},
            {"criterion": "problem_solving_clarity", "rating": "PARTIAL", "evidence": []},
            {"criterion": "claim_vs_transcript_proof", "rating": "PARTIAL", "evidence": []},
        ],
        "claim_findings": [],
        "recommendation": "ADVANCE",
        "whisper": "Test",
        "reasoning": "Test",
    }
    client = FakeLLMClient(json_response=canned)
    result = technical_evaluator.run(dossier, client)

    # STRONG should be downgraded to NOT_DEMONSTRATED because no quotes verified
    rating_map = {r.criterion: r.rating for r in result.ratings}
    assert rating_map["core_technical_depth"] == "NOT_DEMONSTRATED"
    assert len(result.violations) > 0
    assert "core_technical_depth: STRONG -> NOT_DEMONSTRATED" in result.violations[0]


# 5. Model recommendation overridden by code
def test_model_recommendation_overridden_by_code():
    """Model recommendation (e.g. ADVANCE) is overridden by deterministic scoring."""
    dossier = create_sample_dossier()
    # All ratings NOT_DEMONSTRATED -> score is 0.0 -> code must derive DO_NOT_ADVANCE
    canned = {
        "ratings": [
            {"criterion": "core_technical_depth", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "system_design_reasoning", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "problem_solving_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "claim_vs_transcript_proof", "rating": "NOT_DEMONSTRATED", "evidence": []},
        ],
        "claim_findings": [],
        "recommendation": "ADVANCE",  # Model claims ADVANCE despite 0 ratings
        "whisper": "Test",
        "reasoning": "Test",
    }
    client = FakeLLMClient(json_response=canned)
    result = technical_evaluator.run(dossier, client)

    assert result.recommendation == "DO_NOT_ADVANCE"


# 6. Chair failure returns placeholder
def test_chair_failure_returns_placeholder():
    """When the LLM client raises an exception, the chair returns placeholder text."""
    client = FakeLLMClient(should_fail=True)
    gate = {"decision": "DO_NOT_ADVANCE", "council_score": 0.25}
    evals = {
        "TECHNICAL": AgentEval(
            agent="TECHNICAL",
            ratings=[
                CriterionRating(criterion="core_technical_depth", rating="NOT_DEMONSTRATED")
            ],
            recommendation="DO_NOT_ADVANCE",
        )
    }
    points = [
        Point(
            id="P1",
            rule="skill_not_demonstrated",
            severity="high",
            challenger="TECHNICAL",
            challenged="DELIVERY",
            detail="detail",
        )
    ]
    summary = chair.run(gate, evals, points, client)
    assert summary.startswith("(chair unavailable:")
    assert "Fake network failure" in summary


# 7. Extractor drops non-verbatim claims
def test_extractor_drops_non_verbatim_claims():
    """Extractor drops any extracted claim whose resume_quote is not verbatim in resume."""
    resume_text = "Senior Python Developer. Maintained Postgres databases."
    canned_claims = {
        "claims": [
            {
                "id": "C1",
                "text": "Maintained Postgres databases",
                "category": "technical",
                "resume_quote": "Maintained Postgres databases.",
            },
            {
                "id": "C2",
                "text": "Architected Kubernetes cluster from scratch",
                "category": "delivery",
                "resume_quote": "Architected Kubernetes cluster from scratch.",  # NOT in resume
            },
        ]
    }
    client = FakeLLMClient(json_response=canned_claims)
    kept, warnings = extractor.run(resume_text, client)

    assert len(kept) == 1
    assert kept[0].id == "C1"
    assert kept[0].text == "Maintained Postgres databases"
    assert any("dropped claim" in w for w in warnings)


# 8. Moderator skips on empty points and revises losing agent
def test_moderator_skips_when_no_points():
    """Moderator makes no LLM calls and returns (False, []) when there are no points."""
    client = FakeLLMClient()
    argued, revisions = moderator.run({}, [], client)
    assert argued is False
    assert revisions == []
    assert len(client.calls) == 0


def test_moderator_revises_losing_agent():
    """Moderator executes batched debate and updates the losing agent's recommendation."""
    point = Point(
        id="P1",
        rule="claim_contradicted",
        severity="high",
        challenger="TECHNICAL",
        challenged="DELIVERY",
        detail="C1 contradicted",
    )
    evals = {
        "TECHNICAL": AgentEval(
            agent="TECHNICAL",
            ratings=[],
            recommendation="DO_NOT_ADVANCE",
        ),
        "DELIVERY": AgentEval(
            agent="DELIVERY",
            ratings=[],
            recommendation="ADVANCE",
        ),
    }
    canned_rulings = {
        "rulings": [
            {
                "point_id": "P1",
                "challenge": "Candidate admitted lead did the cluster work",
                "defense": "none exists",
                "verdict": "challenger",
                "revised_recommendation": "REVIEW",
            }
        ]
    }
    client = FakeLLMClient(json_response=canned_rulings)
    argued, revisions = moderator.run(evals, [point], client)

    assert argued is True
    assert point.verdict == "challenger"
    # Challenger was TECHNICAL, challenged was DELIVERY; verdict was challenger -> loser is DELIVERY
    assert evals["DELIVERY"].recommendation == "REVIEW"
    assert len(revisions) == 1
    assert "DELIVERY: ADVANCE -> REVIEW (P1)" in revisions[0]


# 9. Manager and HR agent personas
def test_manager_and_hr_evaluators_execute():
    """Manager and HR agent correctly bind their persona and criteria."""
    dossier = create_sample_dossier()

    def make_canned(criteria_list):
        return {
            "ratings": [{"criterion": c, "rating": "STRONG", "evidence": []} for c in criteria_list],
            "claim_findings": [],
            "recommendation": "ADVANCE",
            "whisper": "Good candidate",
            "reasoning": "Well qualified",
        }

    mgr_client = FakeLLMClient(
        json_response=make_canned(
            ["shipped_outcomes", "ownership", "business_impact", "seniority_fit"]
        )
    )
    mgr_eval = manager.run(dossier, mgr_client)
    assert mgr_eval.agent == "DELIVERY"
    assert len(mgr_eval.ratings) == 4

    hr_client = FakeLLMClient(
        json_response=make_canned(
            ["communication_clarity", "conflict_handling", "teamwork_evidence", "answer_consistency"]
        )
    )
    hr_eval = hr_agent.run(dossier, hr_client)
    assert hr_eval.agent == "COLLABORATION"
    assert len(hr_eval.ratings) == 4
