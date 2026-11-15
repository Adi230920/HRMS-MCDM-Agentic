"""End-to-end verification script for TalentCouncil HRMS.

Posts the three canonical samples (hire, reject, review), waits for completion,
and validates PRD success criteria:
- Decision matches expected for 3 of 3 samples
- Duration under 120 seconds
- At most 7 LLM calls per run
- Identical replay on stored outputs
- No raw PII stored in database
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.db.models import (
    LLMCall,
    Review,
    Run,
    RunArtifact,
    RunInput,
    get_session,
    init_db,
)


def load_samples() -> list[dict]:
    """Load the three canonical samples from prep/samples or backend/samples."""
    sample_files = ["hire.json", "reject.json", "review.json"]
    samples = []
    for fname in sample_files:
        p = PROJECT_ROOT / "prep" / "samples" / fname
        if not p.is_file():
            p = PROJECT_ROOT / "backend" / "samples" / fname
        if not p.is_file():
            p = PROJECT_ROOT / "samples" / fname
        if not p.is_file():
            raise FileNotFoundError(f"Cannot locate sample file: {fname}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_filename"] = fname
            samples.append(data)
    return samples


class ApiRunner:
    """Handles communication with the backend either via HTTP or FastAPI TestClient."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.is_live = False
        self.client = None

        # Probe if live backend is running
        try:
            req = urllib.request.Request(f"{self.base_url}/api/health", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    self.is_live = True
        except Exception:
            self.is_live = False

        if not self.is_live:
            from fastapi.testclient import TestClient
            from backend.app.main import app

            init_db()
            self.client = TestClient(app)

    def post_run(self, payload: dict, mock: bool = True) -> dict:
        url_path = f"/api/runs{'?mock=true' if mock else ''}"
        if self.is_live:
            req = urllib.request.Request(
                f"{self.base_url}{url_path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            resp = self.client.post(url_path, json=payload)
            return resp.json()

    def get_run(self, run_id: str) -> dict:
        url_path = f"/api/runs/{run_id}"
        if self.is_live:
            req = urllib.request.Request(f"{self.base_url}{url_path}", method="GET")
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            resp = self.client.get(url_path)
            return resp.json()

    def post_replay(self, run_id: str) -> dict:
        url_path = f"/api/runs/{run_id}/replay"
        if self.is_live:
            req = urllib.request.Request(f"{self.base_url}{url_path}", data=b"{}", method="POST")
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            resp = self.client.post(url_path)
            return resp.json()

    def wait_for_run(self, run_id: str, timeout: float = 120.0) -> dict:
        start_time = time.time()
        while time.time() - start_time < timeout:
            run_data = self.get_run(run_id)
            status = run_data.get("status")
            if status in ("COMPLETED", "FAILED"):
                return run_data
            time.sleep(0.5)
        raise TimeoutError(f"Run {run_id} timed out after {timeout} seconds")


def check_pii_in_db(run_id: str, sample: dict) -> bool:
    """Inspect SQLite database records for any unredacted PII from the candidate."""
    raw_pii_tokens = []
    cand_name = sample.get("candidate_name", "").strip()
    if cand_name:
        for part in cand_name.split():
            if len(part) > 2:
                raw_pii_tokens.append(part)

    # Known candidate PII tokens from samples
    if "priya" in cand_name.lower():
        raw_pii_tokens.extend(["priya@example.com", "98765 43210", "9876543210"])

    if not raw_pii_tokens:
        return False

    session = get_session()
    try:
        # Check RunInput
        inp = session.query(RunInput).filter(RunInput.run_id == run_id).first()
        if inp:
            for token in raw_pii_tokens:
                if (
                    token.lower() in inp.resume_redacted.lower()
                    or token.lower() in inp.transcript_redacted.lower()
                ):
                    return True

        # Check RunArtifacts
        artifacts = session.query(RunArtifact).filter(RunArtifact.run_id == run_id).all()
        for art in artifacts:
            for token in raw_pii_tokens:
                if token.lower() in art.content.lower():
                    return True

        # Check LLMCall
        calls = session.query(LLMCall).filter(LLMCall.run_id == run_id).all()
        for c in calls:
            for token in raw_pii_tokens:
                if c.error and token.lower() in c.error.lower():
                    return True

        # Check Run
        run = session.query(Run).filter(Run.id == run_id).first()
        if run:
            for token in raw_pii_tokens:
                if run.cache_key and token.lower() in run.cache_key.lower():
                    return True
                if run.error and token.lower() in run.error.lower():
                    return True
    finally:
        session.close()

    return False


def main() -> None:
    print("=" * 110)
    print("TalentCouncil HRMS - End-to-End Verification (Mock Mode)")
    print("=" * 110)

    runner = ApiRunner()
    mode_desc = "Live HTTP (http://127.0.0.1:8000)" if runner.is_live else "In-process FastAPI TestClient"
    print(f"Runner mode: {mode_desc}\n")

    samples = load_samples()
    results = []
    all_passed = True

    for sample in samples:
        fname = sample["_filename"]
        expected = sample.get("expected", "")
        payload = {
            "jd": sample.get("jd", ""),
            "resume": sample.get("resume", ""),
            "transcript": sample.get("transcript", ""),
            "candidate_name": sample.get("candidate_name", ""),
        }

        t0 = time.time()
        create_res = runner.post_run(payload, mock=True)
        run_id = create_res.get("run_id")

        if not run_id:
            print(f"FAILED to start run for sample {fname}: {create_res}")
            sys.exit(1)

        run_detail = runner.wait_for_run(run_id)
        duration = time.time() - t0

        decision = run_detail.get("decision", "UNKNOWN")
        council_score = run_detail.get("council_score", 0.0)
        llm_calls = len(run_detail.get("llm_calls", []))

        # Check debate argued
        artifacts = run_detail.get("artifacts", {})
        if "argued" in artifacts:
            argued = bool(artifacts["argued"])
        else:
            trace = artifacts.get("trace", [])
            argued = any(isinstance(step, (list, tuple)) and step[0] == "debate" for step in trace)

        # Check PII in DB
        pii_found = check_pii_in_db(run_id, sample)

        # Check replay identical
        replay_res = runner.post_replay(run_id)
        replay_identical = replay_res.get("identical", False)

        # Check criteria
        match = (decision == expected)
        duration_ok = (duration < 120.0)
        calls_ok = (llm_calls <= 7)
        no_pii_ok = (not pii_found)
        replay_ok = replay_identical

        passed = match and duration_ok and calls_ok and no_pii_ok and replay_ok
        if not passed:
            all_passed = False

        results.append({
            "sample": fname,
            "expected": expected,
            "decision": decision,
            "council_score": council_score if council_score is not None else 0.0,
            "debate_argued": "yes" if argued else "no",
            "llm_calls": llm_calls,
            "duration": duration,
            "pii_found": "yes" if pii_found else "no",
            "replay_identical": "yes" if replay_ok else "no",
            "match": match,
            "criteria_ok": passed,
        })

    # Print Table
    header = f"{'Sample':<12} | {'Expected':<14} | {'Decision':<14} | {'Council Score':<13} | {'Debate Argued':<13} | {'LLM Calls':<9} | {'Duration':<9} | {'PII in DB':<9} | {'Replay Identical':<16}"
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)

    matching_count = 0
    for r in results:
        if r["match"]:
            matching_count += 1
        print(
            f"{r['sample']:<12} | "
            f"{r['expected']:<14} | "
            f"{r['decision']:<14} | "
            f"{r['council_score']:<13.3f} | "
            f"{r['debate_argued']:<13} | "
            f"{r['llm_calls']:<9} | "
            f"{r['duration']:<8.2f}s | "
            f"{r['pii_found']:<9} | "
            f"{r['replay_identical']:<16}"
        )
    print(sep)
    print(f"\nResult: {matching_count} of {len(results)} matching expected decisions.")

    # PRD Success Criteria Check
    print("\nPRD Success Criteria Checks:")
    print(f"  - 3 of 3 matching decisions:     {'PASS' if matching_count == 3 else 'FAIL'}")
    print(f"  - All runs under 120 seconds:    {'PASS' if all(r['duration'] < 120.0 for r in results) else 'FAIL'}")
    print(f"  - At most 7 LLM calls per run:   {'PASS' if all(r['llm_calls'] <= 7 for r in results) else 'FAIL'}")
    print(f"  - Replay identical across runs:  {'PASS' if all(r['replay_identical'] == 'yes' for r in results) else 'FAIL'}")
    print(f"  - No raw PII stored in DB:       {'PASS' if all(r['pii_found'] == 'no' for r in results) else 'FAIL'}")

    if all_passed and matching_count == 3:
        print("\nALL PRD SUCCESS CRITERIA PASSED.")
        sys.exit(0)
    else:
        print("\nSOME CHECKS FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()

