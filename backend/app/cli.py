"""TalentCouncil CLI for running candidate evaluations live or with mock replay."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path so backend.app is always canonical
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
backend_root = project_root / "backend"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.graph.pipeline import run_council, show
from backend.tests.fixtures.samples import MockReplayLLMClient


def resolve_sample_path(raw_path: str) -> Path:
    """Resolve sample file path across repo root and backend directory."""
    p = Path(raw_path)
    if p.is_file():
        return p

    # Try relative to backend dir
    backend_candidate = backend_root / raw_path
    if backend_candidate.is_file():
        return backend_candidate

    # Try backend/samples
    backend_samples = backend_root / "samples" / p.name
    if backend_samples.is_file():
        return backend_samples

    # Try root/samples
    repo_samples = project_root / "samples" / p.name
    if repo_samples.is_file():
        return repo_samples

    raise FileNotFoundError(f"Could not locate sample file at '{raw_path}'")


def cmd_run(args: argparse.Namespace) -> None:
    """Execute pipeline on a sample file."""
    sample_file = resolve_sample_path(args.sample_path)
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    jd = data.get("jd", "")
    resume = data.get("resume", "")
    transcript = data.get("transcript", "")
    candidate_name = data.get("candidate_name", "")
    sample_id = data.get("id", sample_file.stem)

    client = MockReplayLLMClient(sample_id) if args.mock else None

    result = run_council(
        jd=jd,
        resume=resume,
        transcript=transcript,
        candidate_name=candidate_name,
        llm_client=client,
    )
    show(result)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="TalentCouncil HRMS Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run council pipeline on a sample JSON file")
    run_parser.add_argument("sample_path", help="Path to sample JSON file")
    run_parser.add_argument(
        "--mock",
        action="store_true",
        help="Replay recorded outputs from tests/fixtures instead of live LLM calls",
    )

    args = parser.parse_args()
    if args.command == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
