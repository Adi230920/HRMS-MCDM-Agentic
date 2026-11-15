"""Core domain models and evaluation schemas."""

from typing import Literal

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


class Rulings(BaseModel):
    rulings: list[Ruling]

