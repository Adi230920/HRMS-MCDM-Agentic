"""Delivery manager agent (DELIVERY) assessing outcomes and ownership."""

from typing import Any

from backend.app.agents.base import run_agent
from backend.app.core.schemas import AgentEval, Dossier

AGENT_NAME = "DELIVERY"

CONFIG = {
    "persona": "Engineering Director",
    "focus": "whether the candidate shipped and owned outcomes, or contributed peripherally",
    "criteria": [
        "shipped_outcomes",
        "ownership",
        "business_impact",
        "seniority_fit",
    ],
    "red_flags": (
        "led or architected claims where the transcript shows documentation or minor tasks, "
        "someone else handled the hard parts, no measurable result, scope smaller than target role."
    ),
}


def run(dossier: Dossier, llm_client: Any) -> AgentEval:
    """Run DELIVERY evaluator on dossier."""
    return run_agent(AGENT_NAME, CONFIG, dossier, llm_client)

