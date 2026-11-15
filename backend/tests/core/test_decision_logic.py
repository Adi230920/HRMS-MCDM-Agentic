"""Unit tests for scoring, conflict detection rules, and deterministic gate logic."""

import pytest

from backend.app.core.gate import deterministic_gate
from backend.app.core.policy import load_policy
from backend.app.core.rules import Point, detect_conflicts
from backend.app.core.schemas import (
    AgentEval,
    Claim,
    ClaimFinding,
    CriterionRating,
    Dossier,
    Evidence,
)
from backend.app.core.scoring import recommend_from_score, score


def _make_eval(
    agent_name: str,
    ratings_dict: dict[str, str],
    claim_findings: list[ClaimFinding] | None = None,
    violations: list[str] | None = None,
) -> AgentEval:
    ratings = [
        CriterionRating(criterion=crit, rating=r, evidence=[])
        for crit, r in ratings_dict.items()
    ]
    ev = AgentEval(
        agent=agent_name,
        ratings=ratings,
        claim_findings=claim_findings or [],
        recommendation="REVIEW",
        violations=violations or [],
    )
    s = score(ev)
    ev.recommendation = recommend_from_score(s)
    return ev


def test_scoring_and_recommendation_derivation():
    policy = load_policy()
    # 4 STRONG ratings: 4 * 1.0 / 4 = 1.0 -> ADVANCE
    strong_eval = _make_eval(
        "TECHNICAL",
        {
            "core_technical_depth": "STRONG",
            "system_design_reasoning": "STRONG",
            "problem_solving_clarity": "STRONG",
            "claim_vs_transcript_proof": "STRONG",
        },
    )
    assert score(strong_eval, policy) == 1.0
    assert strong_eval.recommendation == "ADVANCE"

    # 4 NOT_DEMONSTRATED: 0.0 -> DO_NOT_ADVANCE
    reject_eval = _make_eval(
        "TECHNICAL",
        {
            "core_technical_depth": "NOT_DEMONSTRATED",
            "system_design_reasoning": "NOT_DEMONSTRATED",
            "problem_solving_clarity": "NOT_DEMONSTRATED",
            "claim_vs_transcript_proof": "NOT_DEMONSTRATED",
        },
    )
    assert score(reject_eval, policy) == 0.0
    assert reject_eval.recommendation == "DO_NOT_ADVANCE"

    # 2 PARTIAL, 2 NOT_DEMONSTRATED: (0.5 + 0.5) / 4 = 0.25 -> DO_NOT_ADVANCE
    assert recommend_from_score(0.25, policy) == "DO_NOT_ADVANCE"
    # 0.50 -> REVIEW
    assert recommend_from_score(0.50, policy) == "REVIEW"


def test_conflict_rule_claim_contradicted():
    dossier = Dossier(
        jd="JD",
        resume="Resume",
        turns=[],
        claims=[Claim(id="C1", text="Built auth", category="technical", resume_quote="auth")],
    )
    evals = {
        "TECHNICAL": _make_eval(
            "TECHNICAL",
            {"core_technical_depth": "STRONG"},
            claim_findings=[
                ClaimFinding(
                    claim_id="C1",
                    status="SUPPORTED",
                    evidence=[Evidence(source="transcript", quote="quote")],
                )
            ],
        ),
        "DELIVERY": _make_eval(
            "DELIVERY",
            {"ownership": "STRONG"},
            claim_findings=[
                ClaimFinding(
                    claim_id="C1",
                    status="CONTRADICTED",
                    evidence=[Evidence(source="transcript", quote="quote")],
                )
            ],
        ),
    }
    pts = detect_conflicts(evals, dossier)
    rules = [p.rule for p in pts]
    assert "claim_contradicted" in rules


def test_conflict_rule_seniority_unsupported_and_manager_suppression():
    dossier = Dossier(
        jd="JD",
        resume="Resume",
        turns=[],
        claims=[
            Claim(
                id="C1",
                text="Architected distributed vector database",
                category="technical",
                resume_quote="quote",
            )
        ],
    )
    # When DELIVERY marks UNVERIFIED, seniority_unsupported triggers
    evals1 = {
        "TECHNICAL": _make_eval("TECHNICAL", {"core_technical_depth": "STRONG"}),
        "DELIVERY": _make_eval(
            "DELIVERY",
            {"ownership": "STRONG"},
            claim_findings=[ClaimFinding(claim_id="C1", status="UNVERIFIED")],
        ),
    }
    pts1 = detect_conflicts(evals1, dossier)
    assert any(p.rule == "seniority_unsupported" for p in pts1)

    # When manager (DELIVERY) marks CONTRADICTED, seniority_unsupported is suppressed
    evals2 = {
        "TECHNICAL": _make_eval("TECHNICAL", {"core_technical_depth": "STRONG"}),
        "DELIVERY": _make_eval(
            "DELIVERY",
            {"ownership": "STRONG"},
            claim_findings=[ClaimFinding(claim_id="C1", status="CONTRADICTED")],
        ),
    }
    pts2 = detect_conflicts(evals2, dossier)
    assert not any(p.rule == "seniority_unsupported" for p in pts2)


def test_conflict_rule_skill_not_demonstrated():
    dossier = Dossier(jd="JD", resume="Resume", turns=[], claims=[])
    evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"core_technical_depth": "NOT_DEMONSTRATED"}),
        "DELIVERY": _make_eval(
            "DELIVERY",
            {
                "shipped_outcomes": "STRONG",
                "ownership": "STRONG",
                "business_impact": "STRONG",
                "seniority_fit": "STRONG",
            },
        ),
    }
    pts = detect_conflicts(evals, dossier)
    assert any(p.rule == "skill_not_demonstrated" for p in pts)


def test_conflict_rule_charisma_gap():
    dossier = Dossier(jd="JD", resume="Resume", turns=[], claims=[])
    evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"core_technical_depth": "NOT_DEMONSTRATED"}),
        "COLLABORATION": _make_eval(
            "COLLABORATION",
            {
                "communication_clarity": "STRONG",
                "conflict_handling": "PARTIAL",
                "teamwork_evidence": "PARTIAL",
                "answer_consistency": "PARTIAL",
            },
        ),
    }
    pts = detect_conflicts(evals, dossier)
    assert any(p.rule == "charisma_gap" for p in pts)


def test_conflict_rule_directional_split():
    dossier = Dossier(jd="JD", resume="Resume", turns=[], claims=[])
    evals = {
        "TECHNICAL": _make_eval(
            "TECHNICAL",
            {
                "core_technical_depth": "STRONG",
                "system_design_reasoning": "STRONG",
                "problem_solving_clarity": "STRONG",
                "claim_vs_transcript_proof": "STRONG",
            },
        ),
        "COLLABORATION": _make_eval(
            "COLLABORATION",
            {
                "communication_clarity": "NOT_DEMONSTRATED",
                "conflict_handling": "NOT_DEMONSTRATED",
                "teamwork_evidence": "NOT_DEMONSTRATED",
                "answer_consistency": "NOT_DEMONSTRATED",
            },
        ),
    }
    pts = detect_conflicts(evals, dossier)
    assert any(p.rule == "directional_split" for p in pts)


def test_conflict_rule_ownership_inconsistent():
    dossier = Dossier(jd="JD", resume="Resume", turns=[], claims=[])
    evals = {
        "DELIVERY": _make_eval("DELIVERY", {"ownership": "STRONG"}),
        "COLLABORATION": _make_eval(
            "COLLABORATION", {"answer_consistency": "NOT_DEMONSTRATED"}
        ),
    }
    pts = detect_conflicts(evals, dossier)
    assert any(p.rule == "ownership_inconsistent" for p in pts)


def test_conflict_rule_specialist_dissent():
    dossier = Dossier(jd="JD", resume="Resume", turns=[], claims=[])
    # Technical scores 0.375 (< 0.45, recommendation REVIEW), Delivery recommends ADVANCE (1.0)
    evals = {
        "TECHNICAL": _make_eval(
            "TECHNICAL",
            {
                "core_technical_depth": "PARTIAL",
                "system_design_reasoning": "PARTIAL",
                "problem_solving_clarity": "PARTIAL",
                "claim_vs_transcript_proof": "NOT_DEMONSTRATED",
            },
        ),
        "DELIVERY": _make_eval(
            "DELIVERY",
            {
                "shipped_outcomes": "STRONG",
                "ownership": "STRONG",
                "business_impact": "STRONG",
                "seniority_fit": "STRONG",
            },
        ),
    }
    pts = detect_conflicts(evals, dossier)
    assert any(p.rule == "specialist_dissent" for p in pts)


def test_conflict_rule_citation_unearned_and_points_cap():
    dossier = Dossier(jd="JD", resume="Resume", turns=[], claims=[])
    evals = {
        "TECHNICAL": _make_eval(
            "TECHNICAL",
            {"core_technical_depth": "STRONG"},
            violations=["downgraded rating"],
        ),
    }
    pts = detect_conflicts(evals, dossier)
    assert any(p.rule == "citation_unearned" for p in pts)
    assert len(pts) <= 4


def test_quorum_failure_gives_review():
    evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "STRONG"}),  # ADVANCE (1.0)
        "DELIVERY": _make_eval("DELIVERY", {"c": "PARTIAL"}),  # REVIEW (0.5)
        "COLLABORATION": _make_eval(
            "COLLABORATION", {"c": "NOT_DEMONSTRATED"}
        ),  # DO_NOT_ADVANCE (0.0)
    }
    gate = deterministic_gate(evals, points=[])
    assert gate["quorum"] is False
    assert gate["decision"] == "REVIEW"


def test_one_veto_signal_does_nothing_two_signals_raise_caution():
    # Only 1 signal: technical floor < 0.35, but manager is high and no contradicted claims
    evals1 = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "NOT_DEMONSTRATED"}),  # 0.0 < 0.35
        "DELIVERY": _make_eval("DELIVERY", {"c": "STRONG"}),  # 1.0
        "COLLABORATION": _make_eval("COLLABORATION", {"c": "STRONG"}),  # 1.0
    }
    gate1 = deterministic_gate(evals1, points=[])
    assert len(gate1["veto_signals"]) == 1
    assert gate1["veto"] is False

    # 2 signals: technical floor < 0.35 and delivery floor < 0.35
    evals2 = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "NOT_DEMONSTRATED"}),  # signal 1
        "DELIVERY": _make_eval("DELIVERY", {"c": "NOT_DEMONSTRATED"}),  # signal 2
        "COLLABORATION": _make_eval("COLLABORATION", {"c": "STRONG"}),
    }
    gate2 = deterministic_gate(evals2, points=[])
    assert gate2["veto"] is True
    assert len(gate2["veto_signals"]) >= 2
    # Even if quorum was somehow ADVANCE, veto would lift it to REVIEW


def test_score_penalties_unresolved_and_failed_agent():
    # Base setup: all 1.0
    evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "STRONG"}),
        "DELIVERY": _make_eval("DELIVERY", {"c": "STRONG"}),
        "COLLABORATION": _make_eval("COLLABORATION", {"c": "STRONG"}),
    }
    base_gate = deterministic_gate(evals, points=[])
    assert base_gate["base_score"] == 1.0
    assert base_gate["council_score"] == 1.0

    # 1 unresolved point -> multiplied by (1 - 0.15) = 0.85
    unresolved_point = Point(
        id="P1",
        rule="test",
        severity="high",
        challenger="A",
        challenged="B",
        detail="detail",
        verdict="unresolved",
    )
    p_gate = deterministic_gate(evals, points=[unresolved_point])
    assert p_gate["council_score"] == pytest.approx(0.85, rel=1e-3)

    # 1 failed agent -> multiplied by (1 - 0.20) = 0.80
    f_gate = deterministic_gate(evals, points=[], failed={"COLLABORATION": "timeout"})
    assert f_gate["council_score"] == pytest.approx(0.80, rel=1e-3)


def test_outliers_and_aar():
    # Alone against council: Tech & Delivery ADVANCE, Collaboration DO_NOT_ADVANCE
    evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "STRONG"}),
        "DELIVERY": _make_eval("DELIVERY", {"c": "STRONG"}),
        "COLLABORATION": _make_eval("COLLABORATION", {"c": "NOT_DEMONSTRATED"}),
    }
    resolved_point = Point(
        id="P1",
        rule="directional_split",
        severity="medium",
        challenger="COLLABORATION",
        challenged="TECHNICAL",
        detail="detail",
        verdict="challenged",  # challenger (COLLABORATION) lost
    )
    gate = deterministic_gate(evals, points=[resolved_point])
    assert "COLLABORATION" in gate["outliers"]
    assert "alone against council" in gate["outliers"]["COLLABORATION"]
    assert "lost P1" in gate["outliers"]["COLLABORATION"]
    # 2 out of 3 agreed with decision ("REVIEW" due to lack of unanimity)
    assert gate["aar"] >= 0.0


def test_handbuilt_profiles():
    # 1. Reject profile: all NOT_DEMONSTRATED
    reject_evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "NOT_DEMONSTRATED"}),
        "DELIVERY": _make_eval("DELIVERY", {"c": "NOT_DEMONSTRATED"}),
        "COLLABORATION": _make_eval("COLLABORATION", {"c": "NOT_DEMONSTRATED"}),
    }
    gate_reject = deterministic_gate(reject_evals, points=[])
    assert gate_reject["decision"] == "DO_NOT_ADVANCE"

    # 2. Hire profile: all STRONG, zero unresolved points
    hire_evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "STRONG"}),
        "DELIVERY": _make_eval("DELIVERY", {"c": "STRONG"}),
        "COLLABORATION": _make_eval("COLLABORATION", {"c": "STRONG"}),
    }
    gate_hire = deterministic_gate(hire_evals, points=[])
    assert gate_hire["decision"] == "ADVANCE"

    # 3. Review profile: Technical and Manager STRONG (ADVANCE), Collaboration between 0.30 and 0.60 (REVIEW)
    review_evals = {
        "TECHNICAL": _make_eval("TECHNICAL", {"c": "STRONG"}),
        "DELIVERY": _make_eval("DELIVERY", {"c": "STRONG"}),
        "COLLABORATION": _make_eval(
            "COLLABORATION",
            {"c1": "STRONG", "c2": "NOT_DEMONSTRATED"},  # 0.50 -> REVIEW
        ),
    }
    gate_review = deterministic_gate(review_evals, points=[])
    assert gate_review["decision"] == "REVIEW"
