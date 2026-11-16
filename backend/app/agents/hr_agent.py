"""HR agent (COLLABORATION) assessing communication and teamwork."""

from typing import Any

from backend.app.agents.base import run_agent
from backend.app.core.schemas import AgentEval, Dossier

AGENT_NAME = "COLLABORATION"

CONFIG = {
    "persona": "Senior Talent Partner",
    "focus": (
        "what transcript answers show about communication, teamwork, code reviews, and mentorship. "
        "Evaluate communication clarity specifically in collaborative, team, and peer review contexts. "
        "Never use career gaps, job stability, background, or culture fit."
    ),
    "criteria": [
        "communication_clarity",
        "conflict_handling",
        "teamwork_evidence",
        "answer_consistency",
    ],
    "red_flags": (
        "dismissive talk about teammates (e.g. 'teammates slow me down'), skipping or devaluing code reviews, "
        "refusing mentorship (e.g. 'juniors should figure things out themselves'), blaming others, "
        "contradicting earlier answers, generic claims with no example."
    ),
}


def run(dossier: Dossier, llm_client: Any) -> AgentEval:
    """Run COLLABORATION evaluator on dossier."""
    return run_agent(AGENT_NAME, CONFIG, dossier, llm_client)

