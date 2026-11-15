"""Deterministic gate combining scores, veto rules, and debate verdicts."""

from collections import Counter
from typing import Any

from backend.app.core.policy import Policy, load_policy
from backend.app.core.rules import Point
from backend.app.core.schemas import AgentEval
from backend.app.core.scoring import claim_status, score

CAUTION = {"ADVANCE": 0, "REVIEW": 1, "DO_NOT_ADVANCE": 2}


def deterministic_gate(
    evals: dict[str, AgentEval],
    points: list[Point],
    failed: dict[str, str] | None = None,
    policy: Policy | None = None,
) -> dict[str, Any]:
    """Execute deterministic decision gate over agent evaluations and debate points."""
    pol = policy or load_policy()
    failed_map = failed or {}

    recs = {n: ev.recommendation for n, ev in evals.items()}
    if recs:
        top, k = Counter(recs.values()).most_common(1)[0]
        quorum = k >= 2
        direction = top if quorum else "REVIEW"
    else:
        quorum = False
        direction = "REVIEW"

    st = claim_status(evals)
    veto_floor = pol.veto.floor

    signals = [
        name
        for name, hit in (
            (
                "contradicted_claim",
                any("CONTRADICTED" in s.values() and "SUPPORTED" not in s.values() for s in st.values())
                or any(p.rule == "claim_contradicted" and p.verdict == "challenger" for p in points),
            ),
            ("technical_floor", "TECHNICAL" in evals and score(evals["TECHNICAL"], pol) < veto_floor),
            ("delivery_floor", "DELIVERY" in evals and score(evals["DELIVERY"], pol) < veto_floor),
        )
        if hit
    ]

    veto = len(signals) >= pol.veto.signals_required
    if veto and CAUTION.get(direction, 1) < CAUTION["REVIEW"]:
        direction = "REVIEW"

    unresolved = sum(p.verdict == "unresolved" for p in points)

    # Unanimity requirement for ADVANCE: zero unresolved points and all agents ADVANCE
    if direction == "ADVANCE" and (unresolved > 0 or any(v != "ADVANCE" for v in recs.values())):
        direction = "REVIEW"

    live_w = sum(pol.agent_weights.get(n, 0.0) for n in evals)
    base = (
        sum(pol.agent_weights.get(n, 0.0) * score(ev, pol) for n, ev in evals.items()) / live_w
        if live_w > 0
        else 0.0
    )

    unresolved_penalty = pol.penalties.per_unresolved_point
    failed_penalty = pol.penalties.per_failed_agent
    conf = base * ((1 - unresolved_penalty) ** unresolved) * ((1 - failed_penalty) ** len(failed_map))

    outliers: dict[str, list[str]] = {}
    for n, r in recs.items():
        others = [v for m, v in recs.items() if m != n]
        if len(others) >= 2 and len(set(others)) == 1 and r != others[0]:
            outliers.setdefault(n, []).append("alone against council")
    for p in points:
        loser = {"challenger": p.challenged, "challenged": p.challenger}.get(p.verdict)
        if loser in evals:
            outliers.setdefault(loser, []).append(f"lost {p.id}")

    aar = sum(v == direction for v in recs.values()) / len(recs) if recs else 0.0

    score_breakdown = {
        "agent_scores": {n: round(score(ev, pol), 3) for n, ev in evals.items()},
        "agent_weights": {n: pol.agent_weights.get(n, 0.0) for n in evals},
        "live_weight_sum": round(live_w, 3),
        "base_score": round(base, 3),
        "unresolved_points_count": unresolved,
        "unresolved_penalty_rate": unresolved_penalty,
        "unresolved_multiplier": round((1 - unresolved_penalty) ** unresolved, 3),
        "failed_agents_count": len(failed_map),
        "failed_penalty_rate": failed_penalty,
        "failed_multiplier": round((1 - failed_penalty) ** len(failed_map), 3),
        "final_council_score": round(conf, 3),
        "formula": f"Base ({round(base, 3)}) * (1 - {unresolved_penalty})^{unresolved} * (1 - {failed_penalty})^{len(failed_map)} = {round(conf, 3)}",
    }

    initial_direction = top if recs else "REVIEW"
    decision_trace = [
        {
            "step": 1,
            "stage": "Quorum & Initial Direction",
            "rule": "Majority recommendation (k >= 2 of panel agents)",
            "status": "PASSED" if quorum else "NOT_MET",
            "detail": f"Agent votes: {recs}. Top recommendation: '{initial_direction}' ({k}/{len(recs)} agents)." if recs else "No agent evaluations present.",
            "outcome": f"Direction set to '{direction}'",
        },
        {
            "step": 2,
            "stage": "Veto Rule Evaluation",
            "rule": f"Veto triggers if >= {pol.veto.signals_required} critical signals trip (threshold floor: {veto_floor})",
            "status": "TRIGGERED" if veto else "CLEARED",
            "detail": f"Active veto signals: {signals if signals else 'None'}. Signals count: {len(signals)}/{pol.veto.signals_required}.",
            "outcome": f"Direction demoted from '{initial_direction}' to 'REVIEW'" if (veto and initial_direction == "ADVANCE") else "No veto demotion applied",
        },
        {
            "step": 3,
            "stage": "Unanimity & Debate Resolution Check",
            "rule": "ADVANCE verdict requires 100% unanimous panel and 0 unresolved debate points",
            "status": "PASSED" if (unresolved == 0 and all(v == "ADVANCE" for v in recs.values())) else "FLAGGED",
            "detail": f"Unresolved points: {unresolved}. Panel unanimity: {all(v == 'ADVANCE' for v in recs.values())}.",
            "outcome": "Direction downgraded to 'REVIEW'" if (direction == "REVIEW" and initial_direction == "ADVANCE" and not veto) else "Maintained current direction",
        },
        {
            "step": 4,
            "stage": "Confidence Penalty Application",
            "rule": f"Base score penalized by {int(unresolved_penalty * 100)}% per unresolved point and {int(failed_penalty * 100)}% per failed agent",
            "status": "PENALIZED" if (unresolved > 0 or len(failed_map) > 0) else "NO_PENALTY",
            "detail": f"Base score: {round(base, 3)}. Score adjusted to {round(conf, 3)}.",
            "outcome": f"Score shifted by {round(conf - base, 3)}",
        },
        {
            "step": 5,
            "stage": "Council Consensus & Alignment",
            "rule": "Post-resolution agreement rate (AAR) and outlier detection",
            "status": "ALIGNED" if aar >= 0.67 else "DIVIDED",
            "detail": f"Agreement After Resolution (AAR): {round(aar * 100, 1)}%. Outliers detected: {outliers if outliers else 'None'}.",
            "outcome": f"Final Council Verdict: '{direction}' (Score: {round(conf, 3)})",
        },
    ]

    return {
        "decision": direction,
        "quorum": quorum,
        "veto": veto,
        "veto_signals": signals,
        "base_score": round(base, 3),
        "council_score": round(conf, 3),
        "unresolved": unresolved,
        "aar": round(aar, 3),
        "outliers": outliers,
        "final": recs,
        "decision_trace": decision_trace,
        "score_breakdown": score_breakdown,
    }
