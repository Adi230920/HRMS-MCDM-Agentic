"""Scoring and recommendation derivation logic."""


from backend.app.core.policy import Policy, load_policy
from backend.app.core.schemas import AgentEval

DEFAULT_POLICY: Policy | None = None


def _get_policy(policy: Policy | None = None) -> Policy:
    global DEFAULT_POLICY
    if policy is not None:
        return policy
    if DEFAULT_POLICY is None:
        DEFAULT_POLICY = load_policy()
    return DEFAULT_POLICY


def score(ev: AgentEval, policy: Policy | None = None) -> float:
    """Calculate average rating score for an agent evaluation."""
    pol = _get_policy(policy)
    if not ev.ratings:
        return 0.0
    points_map = pol.rating_points
    return sum(points_map.get(r.rating, 0.0) for r in ev.ratings) / len(ev.ratings)


def rate(ev: AgentEval, crit: str) -> str:
    """Extract rating for a specific criterion."""
    return next(r.rating for r in ev.ratings if r.criterion == crit)


def recommend_from_score(score_val: float, policy: Policy | None = None) -> str:
    """Derive recommendation from computed score."""
    pol = _get_policy(policy)
    if score_val >= pol.recommend.advance_at:
        return "ADVANCE"
    if score_val < pol.recommend.reject_below:
        return "DO_NOT_ADVANCE"
    return "REVIEW"


def claim_status(evals: dict[str, AgentEval]) -> dict[str, dict[str, str]]:
    """Index claim finding statuses by claim_id and agent name."""
    statuses: dict[str, dict[str, str]] = {}
    for name, ev in evals.items():
        for f in ev.claim_findings:
            statuses.setdefault(f.claim_id, {})[name] = f.status
    return statuses
