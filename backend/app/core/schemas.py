"""Core domain models and evaluation schemas."""

from typing import Any, Literal

from pydantic import BaseModel, field_validator

Rating = Literal["NOT_DEMONSTRATED", "PARTIAL", "STRONG"]
Rec = Literal["ADVANCE", "REVIEW", "DO_NOT_ADVANCE"]
AgentName = Literal["TECHNICAL", "DELIVERY", "COLLABORATION"]


class Turn(BaseModel):
    id: str
    speaker: Literal["INTERVIEWER", "CANDIDATE"]
    text: str


class Claim(BaseModel):
    id: str
    text: str
    category: Literal["technical", "delivery", "collaboration"]
    resume_quote: str


class ClaimList(BaseModel):
    claims: list[Claim]


class Dossier(BaseModel):
    jd: str
    resume: str
    turns: list[Turn]
    claims: list[Claim] = []
    warnings: list[str] = []


class Evidence(BaseModel):
    source: Literal["resume", "transcript"]
    quote: str
    verified: bool = False


class CriterionRating(BaseModel):
    criterion: str
    rating: Rating
    evidence: list[Evidence] = []

    @field_validator("rating", mode="before")
    @classmethod
    def _norm_rating(cls, v: Any) -> Any:
        if isinstance(v, str):
            s = v.strip().upper().replace(" ", "_").replace("-", "_")
            if s in ("NONE", "NO", "NOT", "FAIL", "POOR", "WEAK"):
                return "NOT_DEMONSTRATED"
            if s in ("GOOD", "HIGH", "EXCELLENT"):
                return "STRONG"
            if s in ("MEDIUM", "MODERATE", "SOME"):
                return "PARTIAL"
            return s
        return v


class ClaimFinding(BaseModel):
    claim_id: str
    status: Literal["SUPPORTED", "CONTRADICTED", "UNVERIFIED"]
    evidence: list[Evidence] = []


class AgentEval(BaseModel):
    agent: AgentName | None = None
    ratings: list[CriterionRating]
    claim_findings: list[ClaimFinding] = []
    recommendation: Rec
    whisper: str = ""
    reasoning: str = ""
    violations: list[str] = []

    @field_validator("recommendation", mode="before")
    @classmethod
    def _norm_rec(cls, v: Any) -> Any:
        if isinstance(v, str):
            s = v.strip().upper().replace(" ", "_").replace("-", "_")
            if s in ("REJECT", "DO_NOT_HIRE", "NO", "FAIL"):
                return "DO_NOT_ADVANCE"
            if s in ("HIRE", "PASS", "ACCEPT"):
                return "ADVANCE"
            return s
        return v

    @field_validator("whisper")
    @classmethod
    def _cap(cls, v: str) -> str:
        return " ".join(v.split()[:30])


class Ruling(BaseModel):
    point_id: str
    challenge: str
    defense: str
    verdict: Literal["challenger", "challenged", "unresolved"]
    revised_recommendation: Rec | None = None

    @field_validator("revised_recommendation", mode="before")
    @classmethod
    def _norm_revised(cls, v: Any) -> Any:
        if isinstance(v, str):
            s = v.strip().upper().replace(" ", "_").replace("-", "_")
            if s in ("REJECT", "DO_NOT_HIRE", "NO", "FAIL"):
                return "DO_NOT_ADVANCE"
            if s in ("HIRE", "PASS", "ACCEPT"):
                return "ADVANCE"
            if s in ("NONE", "NULL", ""):
                return None
            return s
        return v


class Rulings(BaseModel):
    rulings: list[Ruling]

