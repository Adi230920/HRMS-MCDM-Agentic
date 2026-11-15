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
    rationale: str = ""
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
    verdict_rationale: str = ""
    key_evidence: list[str] = []
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


class ChairFinding(BaseModel):
    source: str = ""
    observation: str = ""
    evidence_quote: str = ""


class ChairSummary(BaseModel):
    verdict_statement: str
    one_sentence_takeaway: str = ""
    strengths: list[str] = []
    red_flags: list[str] = []
    suggested_followups: list[str] = []
    debate_narrative: str = ""
    key_findings: list[ChairFinding] = []
    risk_factors: list[str] = []
    synthesis_rationale: str = ""

    @classmethod
    def from_text_or_dict(cls, data: Any) -> "ChairSummary":
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            return cls.model_validate(data)
        if isinstance(data, str):
            lines = [line.strip() for line in data.strip().split("\n") if line.strip()]
            verdict = lines[0] if lines else "Council evaluation completed."
            findings = [
                ChairFinding(observation=line.lstrip("-*• ").strip())
                for line in lines[1:]
                if line.lstrip("-*• ").strip()
            ]
            strengths = [f.observation for f in findings if any(w in f.observation.lower() for w in ("demonstrated", "verified", "strong", "high", "success", "proven"))]
            red_flags = [f.observation for f in findings if any(w in f.observation.lower() for w in ("contradict", "unverified", "poor", "risk", "dismiss", "skip", "fail", "split"))]
            return cls(
                verdict_statement=verdict,
                one_sentence_takeaway=verdict,
                strengths=strengths or [f.observation for f in findings[:2]],
                red_flags=red_flags,
                debate_narrative=data,
                key_findings=findings,
                synthesis_rationale=data,
            )
        return cls(verdict_statement=str(data), one_sentence_takeaway=str(data))

    def to_prose(self) -> str:
        findings_bullets = "\n".join(
            f"- [{f.source}] {f.observation}" + (f': "{f.evidence_quote}"' if f.evidence_quote else "")
            for f in self.key_findings
        )
        risks_bullets = "\n".join(f"- {r}" for r in self.risk_factors) if self.risk_factors else "None flagged."
        return (
            f"{self.verdict_statement}\n\n"
            f"Findings:\n{findings_bullets}\n\n"
            f"Risk Factors:\n{risks_bullets}\n\n"
            f"Rationale:\n{self.synthesis_rationale}"
        )

