"""Rule-based conflict detection between agent evaluations."""

import re
from typing import Literal

from pydantic import BaseModel

from backend.app.core.policy import Policy, load_policy
from backend.app.core.schemas import AgentEval, Dossier
from backend.app.core.scoring import claim_status, rate, score

SEVERITY = {"high": 0, "medium": 1, "low": 2}
LEADERSHIP = re.compile(
    r"(?i)\b(led|architected|owned|spearheaded|managed|headed|founded)\b"
)


class Point(BaseModel):
    """Contested debate point between panel agents."""

    id: str
    rule: str
    severity: Literal["high", "medium", "low"]
    challenger: str
    challenged: str
    detail: str
    challenge: str = ""
    defense: str = ""
    verdict: Literal["challenger", "challenged", "unresolved"] = "unresolved"
    verdict_rationale: str = ""
    key_evidence: list[str] = []


def detect_conflicts(
    evals: dict[str, AgentEval],
    dossier: Dossier,
    policy: Policy | None = None,
) -> list[Point]:
    """Detect contested conflict points across evaluating agents."""
    pol = policy or load_policy()
    points: list[Point] = []

    def add(rule: str, sev: Literal["high", "medium", "low"], ch: str, cd: str, detail: str) -> None:
        points.append(
            Point(
                id="",
                rule=rule,
                severity=sev,
                challenger=ch,
                challenged=cd,
                detail=detail,
            )
        )

    st = claim_status(evals)

    # 1. Claim status conflicts and seniority
    for c in dossier.claims:
        s = st.get(c.id, {})
        sup = [a for a, v in s.items() if v == "SUPPORTED"]
        con = [a for a, v in s.items() if v == "CONTRADICTED"]

        if sup and con:
            add(
                "claim_contradicted",
                "high",
                con[0],
                sup[0],
                f"{c.id} '{c.text}': contradicted by {con}, supported by {sup}",
            )
        elif (
            LEADERSHIP.search(c.text)
            and not sup
            and "DELIVERY" in evals
            and s.get("DELIVERY") != "CONTRADICTED"
        ):
            who = next((a for a in evals if a != "DELIVERY"), None)
            if who:
                detail = (
                    f"{c.id} '{c.text}' has no supporting transcript evidence"
                    + (f" (contradicted by {con})" if con else "")
                )
                add("seniority_unsupported", "high", who, "DELIVERY", detail)

    t_eval = evals.get("TECHNICAL")
    d_eval = evals.get("DELIVERY")
    c_eval = evals.get("COLLABORATION")

    # 2. skill_not_demonstrated
    adv = [a for a, ev in evals.items() if ev.recommendation == "ADVANCE" and a != "TECHNICAL"]
    if t_eval and adv and rate(t_eval, "core_technical_depth") == "NOT_DEMONSTRATED":
        add(
            "skill_not_demonstrated",
            "high",
            "TECHNICAL",
            adv[0],
            "Technical found no demonstrated core depth while a peer recommends ADVANCE",
        )

    # 2b. teamwork_not_demonstrated
    adv_c = [a for a, ev in evals.items() if ev.recommendation == "ADVANCE" and a != "COLLABORATION"]
    if c_eval and adv_c and rate(c_eval, "teamwork_evidence") == "NOT_DEMONSTRATED":
        add(
            "teamwork_not_demonstrated",
            "high",
            "COLLABORATION",
            adv_c[0],
            "Collaboration found no demonstrated teamwork or mentorship while a peer recommends ADVANCE",
        )

    # 3. charisma_gap
    if (
        t_eval
        and c_eval
        and rate(c_eval, "communication_clarity") == "STRONG"
        and rate(t_eval, "core_technical_depth") == "NOT_DEMONSTRATED"
    ):
        add(
            "charisma_gap",
            "medium",
            "TECHNICAL",
            "COLLABORATION",
            "Strong communication but no demonstrated technical depth",
        )

    # 4. directional_split
    recs = {a: ev.recommendation for a, ev in evals.items()}
    up = [a for a, r in recs.items() if r == "ADVANCE"]
    down = [a for a, r in recs.items() if r == "DO_NOT_ADVANCE"]
    if up and down:
        add(
            "directional_split",
            "medium",
            down[0],
            up[0],
            f"ADVANCE from {up}, DO_NOT_ADVANCE from {down}",
        )

    # 5. ownership_inconsistent
    if (
        d_eval
        and c_eval
        and rate(d_eval, "ownership") == "STRONG"
        and rate(c_eval, "answer_consistency") == "NOT_DEMONSTRATED"
    ):
        add(
            "ownership_inconsistent",
            "medium",
            "COLLABORATION",
            "DELIVERY",
            "Ownership rated strong but answers were inconsistent",
        )

    # 6. specialist_dissent
    dissent_floor = pol.conflicts.dissent_score_below
    low_scores = [a for a, ev in evals.items() if score(ev, pol) < dissent_floor]
    adv_agents = [a for a, ev in evals.items() if ev.recommendation == "ADVANCE"]
    if low_scores and adv_agents and not any(p.rule == "directional_split" for p in points):
        add(
            "specialist_dissent",
            "medium",
            low_scores[0],
            adv_agents[0],
            f"{low_scores[0]} scores {score(evals[low_scores[0]], pol):.2f} while {adv_agents} recommend ADVANCE",
        )

    # 7. citation_unearned
    for n, ev in evals.items():
        if ev.violations:
            add(
                "citation_unearned",
                "low",
                "RULE",
                n,
                f"{len(ev.violations)} rating/finding(s) downgraded for missing verified quotes",
            )

    points.sort(key=lambda p: SEVERITY[p.severity])
    points = points[: pol.conflicts.max_points]
    for i, p in enumerate(points, 1):
        p.id = f"P{i}"
    return points
