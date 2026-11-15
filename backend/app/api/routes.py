"""FastAPI route handlers for candidate evaluations, SSE streaming, reviews, and replays."""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.gate import deterministic_gate
from backend.app.core.parse import check_injection, parse_transcript
from backend.app.core.policy import load_policy
from backend.app.core.redact import redact
from backend.app.core.rules import detect_conflicts
from backend.app.core.schemas import AgentEval, Claim, Dossier
from backend.app.db.models import (
    LLMCall,
    Review,
    Run,
    RunArtifact,
    RunInput,
    get_db,
    get_session,
)
from backend.app.graph.pipeline import run_council
from backend.app.llm.client import get_call_log
from backend.app.llm.models import DEFAULT_ROUTES, get_route_for_role
from backend.tests.fixtures.samples import MockReplayLLMClient

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

# In-memory buffer for SSE events
_RUN_EVENTS: dict[str, list[dict[str, Any]]] = {}


class CreateRunRequest(BaseModel):
    jd: str = Field(..., description="Job description text")
    resume: str = Field(..., description="Candidate resume text")
    transcript: str = Field(..., description="Interview transcript text")
    candidate_name: str = Field("", description="Optional candidate name for redaction only")


class ReviewRequest(BaseModel):
    decision: str = Field(..., description="Human decision: ADVANCE, REVIEW, or DO_NOT_ADVANCE")
    reviewer: str = Field("", description="Reviewer name or identifier")
    notes: str = Field("", description="Reviewer comments or rationale")


def _get_route_config_str() -> str:
    """Serialize active route configuration for cache key computation."""
    parts = []
    for role in sorted(DEFAULT_ROUTES.keys()):
        try:
            links = get_route_for_role(role)
            parts.append(f"{role}=" + "|".join(f"{l.provider}:{l.model}" for l in links))
        except Exception:  # noqa: BLE001
            parts.append(f"{role}=default")
    return ";".join(parts)


def compute_cache_hash(
    jd: str,
    resume_redacted: str,
    transcript_redacted: str,
    policy_version: float,
    route_config: str,
) -> str:
    """Generate deterministic SHA-256 hash across inputs, policy version, and routes."""
    data = (
        f"jd:{jd.strip()}\n"
        f"resume:{resume_redacted.strip()}\n"
        f"transcript:{transcript_redacted.strip()}\n"
        f"policy:{policy_version}\n"
        f"routes:{route_config}"
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _execute_pipeline_task(
    run_id: str,
    jd: str,
    resume: str,
    transcript: str,
    candidate_name: str,
    mock_mode: bool = False,
) -> None:
    """Execute evaluation pipeline in background, record telemetry, and persist artifacts."""
    db: Session = get_session()
    n0 = len(get_call_log())
    t0 = time.time()

    def sse_callback(event_name: str, data: dict[str, Any]) -> None:
        payload = {"event": event_name, "data": data, "timestamp": time.time()}
        _RUN_EVENTS.setdefault(run_id, []).append(payload)

    # Determine LLM client
    llm_client = None
    if mock_mode or settings.MOCK_LLM:
        # Match fixture by keywords
        key = "review"
        if "priya" in candidate_name.lower() or "default settings" in transcript.lower():
            key = "reject"
        elif "brute-force baseline" in transcript.lower() or "humble" in resume.lower():
            key = "hire"
        llm_client = MockReplayLLMClient(key)

    try:
        pkg = run_council(
            jd=jd,
            resume=resume,
            transcript=transcript,
            candidate_name=candidate_name,
            event_callback=sse_callback,
            llm_client=llm_client,
        )

        run_record = db.query(Run).filter(Run.id == run_id).first()
        if run_record:
            # Clear previous artifacts and calls to prevent duplicates on re-execution
            db.query(RunArtifact).filter(RunArtifact.run_id == run_id).delete()
            db.query(LLMCall).filter(LLMCall.run_id == run_id).delete()

            run_record.status = "COMPLETED"
            run_record.decision = pkg.get("decision")
            run_record.council_score = pkg.get("council_score")
            run_record.base_score = pkg.get("base_score")
            run_record.quorum = pkg.get("quorum")
            run_record.veto = pkg.get("veto")
            run_record.veto_signals = json.dumps(pkg.get("veto_signals", []))
            run_record.unresolved = pkg.get("unresolved")
            run_record.aar = pkg.get("aar")

            # Persist artifacts (serializable representations)
            artifacts = [
                ("gate", json.dumps(pkg.get("gate", {}))),
                ("evals", json.dumps({k: v.model_dump() for k, v in pkg.get("evals", {}).items()})),
                ("points", json.dumps([p.model_dump() for p in pkg.get("points", [])])),
                ("chair", pkg.get("chair", "")),
                ("chair_structured", json.dumps(pkg.get("chair_structured", {}))),
                ("trace", json.dumps(pkg.get("trace", []))),
                ("revisions", json.dumps(pkg.get("revisions", []))),
                ("warnings", json.dumps(pkg.get("warnings", []))),
                ("claims", json.dumps([c.model_dump() for c in pkg.get("claims", [])])),
                ("argued", json.dumps(pkg.get("argued", False))),
            ]
            for art_type, art_content in artifacts:
                db.add(RunArtifact(run_id=run_id, artifact_type=art_type, content=art_content))

            # Record LLM calls made during this run
            if llm_client and hasattr(llm_client, "calls"):
                for call in llm_client.calls:
                    db.add(
                        LLMCall(
                            run_id=run_id,
                            role=call.get("role", "unknown"),
                            provider="mock",
                            model="fixture",
                            tokens=50,
                            latency=0.01,
                            finish_reason="stop",
                            retries=0,
                            error=None,
                        )
                    )
            else:
                current_log = get_call_log()[n0:]
                for entry in current_log:
                    db.add(
                        LLMCall(
                            run_id=run_id,
                            role=entry.role,
                            provider=entry.provider,
                            model=entry.model,
                            tokens=entry.tokens,
                            latency=entry.latency,
                            finish_reason=entry.finish_reason,
                            retries=entry.retries,
                            error=entry.error,
                        )
                    )

            db.commit()

        sse_callback("done", {"run_id": run_id, "decision": pkg.get("decision"), "elapsed": round(time.time() - t0, 1)})

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run_record = db.query(Run).filter(Run.id == run_id).first()
        if run_record:
            run_record.status = "FAILED"
            run_record.error = str(exc)
            db.commit()
        sse_callback("error", {"run_id": run_id, "error": str(exc)})
    finally:
        db.close()


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
def create_run(
    req: CreateRunRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    mock: bool = Query(False, description="Run in mock replay mode without live LLM calls"),
) -> dict[str, Any]:
    """Validate inputs, check cache, redact PII, and launch evaluation pipeline."""
    # 1. Validation: size and speaker labels
    pol = load_policy()
    total_len = len(req.jd) + len(req.resume) + len(req.transcript)
    if total_len > pol.limits.max_input_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input length {total_len} exceeds maximum allowed {pol.limits.max_input_chars}",
        )

    try:
        parse_transcript(req.transcript)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Redact inputs (candidate_name is used for redaction only, NEVER stored or logged)
    redacted_resume = redact(req.resume, req.candidate_name)
    redacted_transcript = redact(req.transcript, req.candidate_name)

    # 3. Cache lookup
    route_config = _get_route_config_str()
    input_hash = compute_cache_hash(
        jd=req.jd,
        resume_redacted=redacted_resume,
        transcript_redacted=redacted_transcript,
        policy_version=pol.version,
        route_config=route_config,
    )

    cached_run = (
        db.query(Run)
        .join(RunInput)
        .filter(RunInput.input_hash == input_hash, Run.status == "COMPLETED")
        .first()
    )
    if cached_run:
        return {
            "run_id": cached_run.id,
            "status": "COMPLETED",
            "cached": True,
            "decision": cached_run.decision,
            "council_score": cached_run.council_score,
        }

    # 4. Create new run & run_inputs (strictly storing REDACTED text only)
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    new_run = Run(id=run_id, status="PROCESSING", cache_key=input_hash)
    new_input = RunInput(
        run_id=run_id,
        jd=req.jd.strip(),
        resume_redacted=redacted_resume,
        transcript_redacted=redacted_transcript,
        input_hash=input_hash,
    )
    db.add(new_run)
    db.add(new_input)
    db.commit()

    # 5. Launch background execution
    background_tasks.add_task(
        _execute_pipeline_task,
        run_id=run_id,
        jd=req.jd,
        resume=req.resume,
        transcript=req.transcript,
        candidate_name=req.candidate_name,
        mock_mode=mock,
    )

    return {"run_id": run_id, "status": "PROCESSING", "cached": False}


@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str, db: Annotated[Session, Depends(get_db)]):
    """Stream real-time SSE progress events for a run."""
    run_record = db.query(Run).filter(Run.id == run_id).first()
    if not run_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    async def event_generator():
        delivered = 0
        timeout = 120.0
        start_time = time.time()

        while time.time() - start_time < timeout:
            events = _RUN_EVENTS.get(run_id, [])
            while delivered < len(events):
                ev = events[delivered]
                delivered += 1
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'])}\n\n"
                if ev["event"] in ("done", "error"):
                    return

            # Check database status
            refreshed = db.query(Run).filter(Run.id == run_id).first()
            if refreshed and refreshed.status in ("COMPLETED", "FAILED") and delivered >= len(events):
                yield f"event: done\ndata: {json.dumps({'run_id': run_id, 'status': refreshed.status})}\n\n"
                return

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Retrieve full run results, artifacts, inputs, and reviews."""
    run_record = db.query(Run).filter(Run.id == run_id).first()
    if not run_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    artifacts = {art.artifact_type: art.content for art in run_record.artifacts}
    reviews = [
        {
            "id": r.id,
            "decision": r.decision,
            "reviewer": r.reviewer,
            "notes": r.notes,
            "created_at": r.created_at.isoformat(),
        }
        for r in run_record.reviews
    ]
    calls = [
        {
            "role": c.role,
            "provider": c.provider,
            "model": c.model,
            "tokens": c.tokens,
            "latency": c.latency,
            "error": c.error,
        }
        for c in run_record.llm_calls
    ]

    return {
        "id": run_record.id,
        "status": run_record.status,
        "created_at": run_record.created_at.isoformat(),
        "decision": run_record.decision,
        "council_score": run_record.council_score,
        "base_score": run_record.base_score,
        "quorum": run_record.quorum,
        "veto": run_record.veto,
        "veto_signals": json.loads(run_record.veto_signals) if run_record.veto_signals else [],
        "unresolved": run_record.unresolved,
        "aar": run_record.aar,
        "error": run_record.error,
        "inputs": {
            "jd": run_record.inputs.jd if run_record.inputs else "",
            "resume_redacted": run_record.inputs.resume_redacted if run_record.inputs else "",
            "transcript_redacted": run_record.inputs.transcript_redacted if run_record.inputs else "",
        },
        "artifacts": {
            k: (
                json.loads(v)
                if k in ("evals", "points", "trace", "revisions", "warnings", "gate", "claims", "argued", "chair_structured")
                else v
            )
            for k, v in artifacts.items()
        },
        "llm_calls": calls,
        "reviews": reviews,
    }


@router.get("/runs")
def list_runs(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    """List all candidate evaluation runs."""
    runs = db.query(Run).order_by(Run.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "decision": r.decision,
            "council_score": r.council_score,
            "quorum": r.quorum,
            "veto": r.veto,
        }
        for r in runs
    ]


@router.post("/runs/{run_id}/replay")
def replay_run(run_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Rerun conflict detection and gate decision logic on stored agent outputs."""
    run_record = db.query(Run).filter(Run.id == run_id).first()
    if not run_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    artifacts = {art.artifact_type: art.content for art in run_record.artifacts}
    if "evals" not in artifacts or not run_record.inputs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot replay run without stored evals and inputs",
        )

    evals_raw = json.loads(artifacts["evals"])
    evals = {k: AgentEval.model_validate(v) for k, v in evals_raw.items()}

    # Reconstruct dossier from stored redacted inputs and claims
    inp = run_record.inputs
    turns = parse_transcript(inp.transcript_redacted)
    warnings = check_injection(inp.resume_redacted + inp.transcript_redacted)
    claims = [Claim.model_validate(c) for c in json.loads(artifacts["claims"])] if "claims" in artifacts else []
    dossier = Dossier(jd=inp.jd, resume=inp.resume_redacted, turns=turns, claims=claims, warnings=warnings)

    pol = load_policy()
    new_points = detect_conflicts(evals, dossier, policy=pol)
    new_gate = deterministic_gate(evals, new_points, failed={}, policy=pol)

    original_gate = {
        "decision": run_record.decision,
        "council_score": run_record.council_score,
        "base_score": run_record.base_score,
        "quorum": run_record.quorum,
        "veto": run_record.veto,
        "unresolved": run_record.unresolved,
        "aar": run_record.aar,
    }

    diff = {}
    for key in original_gate:
        orig_val = original_gate.get(key)
        replay_val = new_gate.get(key)
        if orig_val != replay_val:
            diff[key] = {"original": orig_val, "replay": replay_val}

    return {
        "identical": len(diff) == 0,
        "original": original_gate,
        "replay": new_gate,
        "diff": diff,
    }


@router.post("/runs/{run_id}/review", status_code=status.HTTP_201_CREATED)
def create_review(
    run_id: str,
    req: ReviewRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Store human review decision for a run."""
    run_record = db.query(Run).filter(Run.id == run_id).first()
    if not run_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    rev = Review(
        run_id=run_id,
        decision=req.decision,
        reviewer=req.reviewer,
        notes=req.notes,
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)

    return {
        "id": rev.id,
        "run_id": rev.run_id,
        "decision": rev.decision,
        "reviewer": rev.reviewer,
        "notes": rev.notes,
        "created_at": rev.created_at.isoformat(),
    }


@router.get("/samples")
def list_samples() -> list[dict[str, Any]]:
    """List available test candidate samples."""
    samples_dir = Path(__file__).resolve().parents[2] / "samples"
    if not samples_dir.exists():
        samples_dir = Path("backend/samples")

    samples = []
    if samples_dir.exists():
        for f in sorted(samples_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as sfile:
                    data = json.load(sfile)
                    samples.append(
                        {
                            "id": data.get("id", f.stem),
                            "label": data.get("label", f.stem.upper()),
                            "expected": data.get("expected", ""),
                            "filename": f.name,
                            "jd": data.get("jd", ""),
                            "resume": data.get("resume", ""),
                            "transcript": data.get("transcript", ""),
                            "candidate_name": data.get("candidate_name", ""),
                            "resume_preview": data.get("resume", "")[:120],
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed reading sample file %s: %s", f, exc)
                continue
    return samples


@router.get("/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    pol = load_policy()
    return {"status": "ok", "policy_version": pol.version}
