"""Policy configuration model and loader."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class RecommendPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    advance_at: float
    reject_below: float


class VetoPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    floor: float
    signals_required: int


class PenaltiesPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    per_unresolved_point: float
    per_failed_agent: float


class ConflictsPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_points: int
    dissent_score_below: float


class LimitsPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_input_chars: int
    max_claims: int
    whisper_words: int


class Policy(BaseModel):
    model_config = ConfigDict(frozen=True)
    version: float
    rating_points: dict[str, float]
    agent_weights: dict[str, float]
    recommend: RecommendPolicy
    veto: VetoPolicy
    penalties: PenaltiesPolicy
    conflicts: ConflictsPolicy
    advance_requires_unanimity: bool
    limits: LimitsPolicy
    tuned_on: str


def load_policy(path: str | Path | None = None) -> Policy:
    """Load policy YAML file into frozen Policy model."""
    if path is None:
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parents[2]
        candidate_path = backend_dir / "policy.yaml"
        if candidate_path.is_file():
            target_path = candidate_path
        else:
            target_path = Path("backend/policy.yaml")
    else:
        target_path = Path(path)

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Policy.model_validate(data)
