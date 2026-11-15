"""Technical evaluator agent (TECHNICAL) assessing technical depth and proof."""

from typing import Any

from backend.app.agents.base import run_agent
from backend.app.core.schemas import AgentEval, Dossier

AGENT_NAME = "TECHNICAL"

CONFIG = {
    "persona": "Senior Principal Engineer",
    "focus": "whether transcript answers back the technologies and systems claimed on the resume",
    "criteria": [
        "core_technical_depth",
        "system_design_reasoning",
        "problem_solving_clarity",
        "claim_vs_transcript_proof",
    ],
    "red_flags": (
        "buzzwords without mechanism, wrong explanations, vague answers on listed skills, "
        "we used defaults, credit given to others."
    ),
}


def run(dossier: Dossier, llm_client: Any) -> AgentEval:
    """Run TECHNICAL evaluator on dossier."""
    return run_agent(AGENT_NAME, CONFIG, dossier, llm_client)

