"""Quotation normalization and citation verification logic."""

import re

from backend.app.core.schemas import AgentEval, Dossier, Evidence

_T = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def norm(s: str) -> str:
    """Normalize whitespace and quotes in a string."""
    return re.sub(r"\s+", " ", s.translate(_T)).strip().lower()


def verify(ev: Evidence, d: Dossier) -> bool:
    """Verify that an evidence quote exists verbatim in resume or candidate turns."""
    q = norm(re.sub(r"^\s*(\[T\d+\]\s*)?(CANDIDATE:\s*)?", "", ev.quote, flags=re.IGNORECASE))
    if len(q) < 8:
        return False
    hay = (
        norm(d.resume)
        if ev.source == "resume"
        else norm(" ".join(t.text for t in d.turns if t.speaker == "CANDIDATE"))
    )
    return q in hay


def enforce_citations(ev: AgentEval, d: Dossier) -> AgentEval:
    """Verify citations and downgrade ratings/findings when evidence is unverified."""
    for r in ev.ratings:
        for e in r.evidence:
            e.verified = verify(e, d)
        ok_any = any(e.verified for e in r.evidence)
        ok_tr = any(e.verified and e.source == "transcript" for e in r.evidence)
        new = r.rating
        if r.rating == "STRONG" and not ok_tr:
            new = "PARTIAL" if ok_any else "NOT_DEMONSTRATED"
        elif r.rating == "PARTIAL" and not ok_any:
            new = "NOT_DEMONSTRATED"
        if new != r.rating:
            ev.violations.append(f"{r.criterion}: {r.rating} -> {new} (no verified quote)")
            r.rating = new
    for f in ev.claim_findings:
        for e in f.evidence:
            e.verified = verify(e, d)
        if f.status != "UNVERIFIED" and not any(
            e.verified and e.source == "transcript" for e in f.evidence
        ):
            ev.violations.append(
                f"{f.claim_id}: {f.status} -> UNVERIFIED (no verified transcript quote)"
            )
            f.status = "UNVERIFIED"
    return ev

