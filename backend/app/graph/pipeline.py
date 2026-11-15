"""LangGraph pipeline wiring council evaluation stages, debate, gate, and chair."""

import logging
import operator
import time
from collections.abc import Callable
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.app.agents import (
    chair,
    extractor,
    hr_agent,
    manager,
    moderator,
    technical_evaluator,
)
from backend.app.core.gate import deterministic_gate
from backend.app.core.parse import check_injection, parse_transcript
from backend.app.core.policy import Policy, load_policy
from backend.app.core.redact import redact
from backend.app.core.rules import Point, detect_conflicts
from backend.app.core.schemas import AgentEval, Dossier
from backend.app.llm import client as default_llm_client
from backend.app.llm.client import get_call_log

logger = logging.getLogger(__name__)


class CouncilState(TypedDict, total=False):
    """Typed state passing between pipeline stages."""

    jd: str
    resume: str
    transcript: str
    candidate_name: str
    dossier: Dossier | None
    evals: Annotated[dict[str, AgentEval], operator.or_]
    failed: Annotated[dict[str, str], operator.or_]
    initial: dict[str, str]
    points: list[Point]
    argued: bool
    revisions: list[str]
    gate_result: dict[str, Any]
    chair_summary: Any
    trace: Annotated[list[tuple[str, float]], operator.add]
    llm_calls: int
    llm_client: Any
    event_callback: Callable[[str, dict[str, Any]], None] | None
    policy: Policy | None


def _get_client(state: CouncilState) -> Any:
    return state.get("llm_client") or default_llm_client


def _emit_event(
    state: CouncilState,
    event_name: str,
    data: dict[str, Any],
) -> None:
    callback = state.get("event_callback")
    if callback and callable(callback):
        try:
            callback(event_name, data)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Event callback exception: %s", exc)


def node_ingest(state: CouncilState) -> dict[str, Any]:
    """Ingest, redact, parse transcript, and extract verifiable resume claims."""
    t0 = time.time()
    jd = state.get("jd", "")
    resume = state.get("resume", "")
    transcript = state.get("transcript", "")
    candidate_name = state.get("candidate_name", "")

    if not all(x and x.strip() for x in (jd, resume, transcript)):
        raise ValueError("jd, resume and transcript are all required")

    pol = state.get("policy") or load_policy()
    if len(jd) + len(resume) + len(transcript) > pol.limits.max_input_chars:
        raise ValueError(
            f"Input exceeds {pol.limits.max_input_chars} chars; truncate or chunk it"
        )

    # Ingestion warnings
    warnings = check_injection(resume + transcript)

    # Redact inputs
    redacted_resume = redact(resume, candidate_name)
    redacted_transcript = redact(transcript, candidate_name)

    # Parse transcript
    turns = parse_transcript(redacted_transcript)

    dossier = Dossier(
        jd=jd.strip(),
        resume=redacted_resume,
        turns=turns,
        warnings=warnings,
    )

    # Extract claims via extractor agent
    client = _get_client(state)
    extractor.run(dossier, client)

    elapsed = round(time.time() - t0, 1)
    _emit_event(
        state,
        "ingest_completed",
        {"claims": len(dossier.claims), "warnings": dossier.warnings, "elapsed": elapsed},
    )
    return {"dossier": dossier, "trace": [("ingest", elapsed)]}


def node_agent_technical(state: CouncilState) -> dict[str, Any]:
    """Run TECHNICAL evaluator agent branch."""
    t0 = time.time()
    dossier = state["dossier"]
    client = _get_client(state)
    try:
        ev = technical_evaluator.run(dossier, client)
        elapsed = round(time.time() - t0, 1)
        _emit_event(
            state,
            "agent_completed",
            {"agent": "TECHNICAL", "recommendation": ev.recommendation, "elapsed": elapsed},
        )
        return {"evals": {"TECHNICAL": ev}, "trace": [("agent_technical", elapsed)]}
    except Exception as exc:  # noqa: BLE001
        elapsed = round(time.time() - t0, 1)
        err = str(exc)[:200]
        _emit_event(state, "agent_failed", {"agent": "TECHNICAL", "error": err, "elapsed": elapsed})
        return {"failed": {"TECHNICAL": err}, "trace": [("agent_technical", elapsed)]}


def node_agent_delivery(state: CouncilState) -> dict[str, Any]:
    """Run DELIVERY evaluator agent branch."""
    t0 = time.time()
    dossier = state["dossier"]
    client = _get_client(state)
    try:
        ev = manager.run(dossier, client)
        elapsed = round(time.time() - t0, 1)
        _emit_event(
            state,
            "agent_completed",
            {"agent": "DELIVERY", "recommendation": ev.recommendation, "elapsed": elapsed},
        )
        return {"evals": {"DELIVERY": ev}, "trace": [("agent_delivery", elapsed)]}
    except Exception as exc:  # noqa: BLE001
        elapsed = round(time.time() - t0, 1)
        err = str(exc)[:200]
        _emit_event(state, "agent_failed", {"agent": "DELIVERY", "error": err, "elapsed": elapsed})
        return {"failed": {"DELIVERY": err}, "trace": [("agent_delivery", elapsed)]}


def node_agent_collaboration(state: CouncilState) -> dict[str, Any]:
    """Run COLLABORATION evaluator agent branch."""
    t0 = time.time()
    dossier = state["dossier"]
    client = _get_client(state)
    try:
        ev = hr_agent.run(dossier, client)
        elapsed = round(time.time() - t0, 1)
        _emit_event(
            state,
            "agent_completed",
            {"agent": "COLLABORATION", "recommendation": ev.recommendation, "elapsed": elapsed},
        )
        return {"evals": {"COLLABORATION": ev}, "trace": [("agent_collaboration", elapsed)]}
    except Exception as exc:  # noqa: BLE001
        elapsed = round(time.time() - t0, 1)
        err = str(exc)[:200]
        _emit_event(state, "agent_failed", {"agent": "COLLABORATION", "error": err, "elapsed": elapsed})
        return {"failed": {"COLLABORATION": err}, "trace": [("agent_collaboration", elapsed)]}


def node_conflicts(state: CouncilState) -> dict[str, Any]:
    """Detect contested points across evaluated agents."""
    t0 = time.time()
    evals = state.get("evals", {})
    failed = state.get("failed", {})

    if not evals:
        raise RuntimeError(f"All agents failed: {failed}")

    initial = {n: ev.recommendation for n, ev in evals.items()}
    dossier = state["dossier"]
    pol = state.get("policy") or load_policy()

    points = detect_conflicts(evals, dossier, policy=pol)
    elapsed = round(time.time() - t0, 1)
    _emit_event(
        state,
        "conflicts_detected",
        {"points_count": len(points), "initial_recs": initial, "elapsed": elapsed},
    )
    return {
        "initial": initial,
        "points": points,
        "trace": [("conflicts", elapsed)],
    }


def should_debate(state: CouncilState) -> str:
    """Conditionally route to debate node or skip directly to gate."""
    points = state.get("points", [])
    if points and len(points) > 0:
        return "debate"
    return "gate"


def node_debate(state: CouncilState) -> dict[str, Any]:
    """Execute batched adversarial debate over contested points."""
    t0 = time.time()
    evals = state.get("evals", {})
    points = state.get("points", [])
    client = _get_client(state)

    argued, revisions = moderator.run(evals, points, client)
    elapsed = round(time.time() - t0, 1)
    _emit_event(
        state,
        "debate_completed",
        {"argued": argued, "revisions": revisions, "elapsed": elapsed},
    )
    return {
        "evals": evals,
        "argued": argued,
        "revisions": revisions,
        "trace": [("debate", elapsed)],
    }


def node_gate(state: CouncilState) -> dict[str, Any]:
    """Execute deterministic gate decision calculation."""
    t0 = time.time()
    evals = state.get("evals", {})
    points = state.get("points", [])
    failed = state.get("failed", {})
    pol = state.get("policy") or load_policy()

    gate_result = deterministic_gate(evals, points, failed, policy=pol)
    elapsed = round(time.time() - t0, 1)
    _emit_event(
        state,
        "gate_completed",
        {
            "decision": gate_result["decision"],
            "council_score": gate_result["council_score"],
            "elapsed": elapsed,
        },
    )
    return {"gate_result": gate_result, "trace": [("gate", elapsed)]}


def node_chair(state: CouncilState) -> dict[str, Any]:
    """Synthesize final plain-text executive summary prose."""
    t0 = time.time()
    gate = state.get("gate_result", {})
    evals = state.get("evals", {})
    points = state.get("points", [])
    client = _get_client(state)

    chair_res = chair.run(gate, evals, points, client)
    elapsed = round(time.time() - t0, 1)
    _emit_event(state, "chair_completed", {"elapsed": elapsed})
    return {"chair_summary": chair_res, "trace": [("chair", elapsed)]}


def build_graph() -> StateGraph:
    """Construct compiled LangGraph state workflow."""
    workflow = StateGraph(CouncilState)

    workflow.add_node("ingest", node_ingest)
    workflow.add_node("agent_technical", node_agent_technical)
    workflow.add_node("agent_delivery", node_agent_delivery)
    workflow.add_node("agent_collaboration", node_agent_collaboration)
    workflow.add_node("conflicts", node_conflicts)
    workflow.add_node("debate", node_debate)
    workflow.add_node("gate", node_gate)
    workflow.add_node("chair", node_chair)

    workflow.add_edge(START, "ingest")
    workflow.add_edge("ingest", "agent_technical")
    workflow.add_edge("ingest", "agent_delivery")
    workflow.add_edge("ingest", "agent_collaboration")

    workflow.add_edge("agent_technical", "conflicts")
    workflow.add_edge("agent_delivery", "conflicts")
    workflow.add_edge("agent_collaboration", "conflicts")

    workflow.add_conditional_edges(
        "conflicts",
        should_debate,
        {
            "debate": "debate",
            "gate": "gate",
        },
    )

    workflow.add_edge("debate", "gate")
    workflow.add_edge("gate", "chair")
    workflow.add_edge("chair", END)

    return workflow


_COMPILED_GRAPH = None


def get_compiled_graph():
    """Retrieve or build compiled state graph."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph().compile()
    return _COMPILED_GRAPH


def run_council(
    jd: str,
    resume: str,
    transcript: str,
    candidate_name: str = "",
    event_callback: Callable[[str, dict[str, Any]], None] | None = None,
    llm_client: Any = None,
    policy: Policy | None = None,
) -> dict[str, Any]:
    """Execute complete Council hiring decision pipeline."""
    initial_client = llm_client or default_llm_client
    n0 = len(get_call_log())

    init_state: CouncilState = {
        "jd": jd,
        "resume": resume,
        "transcript": transcript,
        "candidate_name": candidate_name,
        "evals": {},
        "failed": {},
        "trace": [],
        "event_callback": event_callback,
        "llm_client": initial_client,
        "policy": policy,
    }

    graph = get_compiled_graph()
    final_state = graph.invoke(init_state)

    gate_data = final_state.get("gate_result", {})
    dossier = final_state.get("dossier")
    warnings = dossier.warnings if dossier else []
    points = final_state.get("points", [])
    evals = final_state.get("evals", {})
    failed = final_state.get("failed", {})
    initial = final_state.get("initial", {})
    argued = final_state.get("argued", False)
    revisions = final_state.get("revisions", [])
    chair_res = final_state.get("chair_summary", "")
    if hasattr(chair_res, "structured"):
        chair_prose = str(chair_res)
        chair_structured = chair_res.structured.model_dump()
    elif hasattr(chair_res, "to_prose"):
        chair_prose = chair_res.to_prose()
        chair_structured = chair_res.model_dump()
    elif isinstance(chair_res, dict):
        chair_prose = chair_res.get("synthesis_rationale", "")
        chair_structured = chair_res
    else:
        chair_prose = str(chair_res)
        chair_structured = {
            "verdict_statement": chair_prose.split("\n")[0] if chair_prose else "",
            "key_findings": [],
            "risk_factors": [],
            "synthesis_rationale": chair_prose,
        }
    trace = final_state.get("trace", [])

    if hasattr(initial_client, "calls"):
        llm_calls = len(initial_client.calls)
    else:
        llm_calls = len(get_call_log()) - n0

    return {
        **gate_data,
        "gate": gate_data,
        "initial": initial,
        "points": points,
        "argued": argued,
        "revisions": revisions,
        "failed": failed,
        "warnings": warnings,
        "evals": evals,
        "chair": chair_prose,
        "chair_structured": chair_structured,
        "llm_calls": llm_calls,
        "trace": trace,
        "claims": dossier.claims if dossier else [],
    }


def show(p: dict[str, Any]) -> None:
    """Print standard pipeline execution summary as in prototype."""
    print(
        f"DECISION: {p['decision']} | council_score={p['council_score']} | "
        f"AAR={p['aar']:.0%} | quorum={p['quorum']} | veto={p['veto']} {p['veto_signals']}"
    )
    print(f"initial={p['initial']} -> final={p['final']} | revisions={p['revisions']}")
    print(f"debate_argued={p['argued']} | llm_calls={p['llm_calls']} | trace={p['trace']}")
    for pt in p["points"]:
        print(f"  [{pt.severity}] {pt.id} {pt.rule} -> {pt.verdict}: {pt.detail}")
    if p.get("outliers"):
        print("outliers:", p["outliers"])
    if p.get("failed"):
        print("failed agents:", p["failed"])
    if p.get("warnings"):
        print("warnings:", p["warnings"])
    print("\n" + p.get("chair", ""))
