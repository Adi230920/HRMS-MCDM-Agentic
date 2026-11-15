"""Evaluation harness comparing single-LLM baseline, naive majority vote, and full Council.

Runs 10 labelled synthetic cases 3 times each, reporting:
- Modal decision and agreement rate across repeated runs
- Accuracy against ground truth
- Resumes cleanly after interruption via eval/results.jsonl
- Enforces --max-calls-per-day rate limiting
- Generates ASCII table and CSV summary
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.redact import redact
from backend.app.core.schemas import Claim, ClaimList, AgentEval, CriterionRating, ClaimFinding, Evidence, Rulings, Ruling
from backend.app.graph.pipeline import run_council
from backend.tests.fixtures.samples import FIXTURES_BY_KEY, MockReplayLLMClient

RESULTS_FILE = PROJECT_ROOT / "eval" / "results.jsonl"
SUMMARY_CSV = PROJECT_ROOT / "eval" / "summary.csv"
CASES_FILE = PROJECT_ROOT / "eval" / "cases.json"

F_TECH_Q = "We combined BM25 lexical signals with dense embeddings from an all-MiniLM model fine-tuned on our clickstream data. We used reciprocal rank fusion at rank 60 to merge lists. Under heavy load, p99 crept over 50ms, so I implemented query-dependent embedding caching with Redis and quantization (PQ8), which cut latency back to 32ms."
F_DELIV_Q = "I set up Argo Rollouts with automated metric analysis monitoring error rate and latency percentiles. When error rate exceeded 0.1%, it aborted automatically. We tested rollouts with Chaos Mesh injects first."
F_COLLAB_Q = "I set bi-weekly growth pairing sessions with each junior engineer. Two of them led their first cross-functional RFCs last quarter, and all four stepped into independent feature ownership."

G_T1 = "I implemented the endpoints using FastAPI and hooked them into Qdrant using the official Python client. The senior architect specified the data models and indexing parameters, and I wrote the unit tests and service logic cleanly."
G_T2 = "Not at an architectural leadership level. When outages happened, I assisted the on-call senior lead with log inspection and debugging specific service endpoints."
G_T3 = "I communicate very well, submit clean pull requests, and am eager to step up, but I have not formally mentored junior team members yet."

J_T1 = "I owned the Helm charts and cluster configuration, but the corporate security team rejected our first cutover because of root container permissions, so we had an intense debate about privilege escalation."
J_T2 = "We agreed to disagree on the RBAC policy; we deployed with temporary exceptions that still haven't been resolved."
J_T3 = "I hold reviews, though some engineers felt my feedback on their PRs was overly harsh and unyielding."

# Extended fixtures for the 7 new cases
NEW_FIXTURES: dict[str, dict[str, Any]] = {
    "D_subtle_perf_lie": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Spearheaded custom GPU kernel optimizations in Triton, reducing retrieval inference latency by 10x",
                    "category": "technical",
                    "resume_quote": "Spearheaded custom GPU kernel optimizations in Triton, reducing retrieval inference latency by 10x",
                },
                {
                    "id": "C2",
                    "text": "Mentored junior engineers on profiling memory bandwidth",
                    "category": "collaboration",
                    "resume_quote": "Mentored junior engineers on profiling memory bandwidth",
                },
            ]
        },
        "technical": {
            "ratings": [
                {
                    "criterion": "core_technical_depth",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "Actually, we didn't write Triton from scratch; we just bumped the batch_size in the vLLM config file from 8 to 64 and latency dropped. I used the word Triton because vLLM has Triton under the hood."}],
                },
                {"criterion": "system_design_reasoning", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "problem_solving_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "claim_vs_transcript_proof", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "No, I didn't write kernel code myself, our platform vendor provided the container image."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Admitted kernel was provided by vendor; only changed config batch size.",
            "reasoning": "Planted performance optimization claim was contradicted.",
        },
        "delivery": {
            "ratings": [
                {"criterion": "shipped_outcomes", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "ownership", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "business_impact", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "seniority_fit", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Did not own or implement kernel optimization.",
            "reasoning": "Lack of ownership.",
        },
        "collaboration": {
            "ratings": [
                {
                    "criterion": "communication_clarity",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "I shared the vLLM documentation link in our team Slack channel."}],
                },
                {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C2", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "I shared the vLLM documentation link in our team Slack channel."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Mentorship was merely pasting a link in Slack.",
            "reasoning": "No real mentorship or collaborative guidance.",
        },
        "chair": "Verdict: DO_NOT_ADVANCE due to falsified GPU kernel claims and superficial mentorship.",
    },
    "E_subtle_scale_lie": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Architected real-time streaming pipeline supporting 100M daily active users",
                    "category": "technical",
                    "resume_quote": "Architected real-time streaming pipeline supporting 100M daily active users",
                },
                {
                    "id": "C2",
                    "text": "Owned multi-cluster Kubernetes deployment across three cloud regions",
                    "category": "delivery",
                    "resume_quote": "Owned multi-cluster Kubernetes deployment across three cloud regions",
                },
            ]
        },
        "technical": {
            "ratings": [
                {
                    "criterion": "core_technical_depth",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "To be completely transparent, the 100M figure was the projected target for the company roadmap. In production we had about 100 internal test users."}],
                },
                {"criterion": "system_design_reasoning", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "problem_solving_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "claim_vs_transcript_proof", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "To be completely transparent, the 100M figure was the projected target for the company roadmap. In production we had about 100 internal test users."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Exaggerated scale by 6 orders of magnitude.",
            "reasoning": "Claimed 100M DAU but only ran 100 test users.",
        },
        "delivery": {
            "ratings": [
                {
                    "criterion": "shipped_outcomes",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "The cloud consultant firm we hired drew up the multi-region topology. I mostly tracked their Jira tickets."}],
                },
                {"criterion": "ownership", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "business_impact", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "seniority_fit", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C2", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "The cloud consultant firm we hired drew up the multi-region topology. I mostly tracked their Jira tickets."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Third-party agency did multi-region Kubernetes work.",
            "reasoning": "No direct delivery ownership.",
        },
        "collaboration": {
            "ratings": [
                {"criterion": "communication_clarity", "rating": "PARTIAL", "evidence": []},
                {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Passive spectator on agency sync calls.",
            "reasoning": "No senior collaborative leadership.",
        },
        "chair": "Verdict: DO_NOT_ADVANCE due to severe inflation of traffic scale and outsourced architecture.",
    },
    "F_all_strong": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Built hybrid lexical/dense search engine with Vespa and FAISS, serving 5M requests/day at p99 < 35ms",
                    "category": "technical",
                    "resume_quote": "Built hybrid lexical/dense search engine with Vespa and FAISS, serving 5M requests/day at p99 < 35ms",
                },
                {
                    "id": "C2",
                    "text": "Designed and executed zero-downtime canary deployment on EKS Kubernetes",
                    "category": "delivery",
                    "resume_quote": "Designed and executed zero-downtime canary deployment on EKS Kubernetes",
                },
                {
                    "id": "C3",
                    "text": "Established weekly architecture review and mentored 4 junior engineers into mid-level roles",
                    "category": "collaboration",
                    "resume_quote": "Established weekly architecture review and mentored 4 junior engineers into mid-level roles",
                },
            ]
        },
        "technical": {
            "ratings": [
                {"criterion": "core_technical_depth", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_TECH_Q}]},
                {"criterion": "system_design_reasoning", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_TECH_Q}]},
                {"criterion": "problem_solving_clarity", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_TECH_Q}]},
                {"criterion": "claim_vs_transcript_proof", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_TECH_Q}]},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "SUPPORTED", "evidence": [{"source": "transcript", "quote": F_TECH_Q}]}
            ],
            "recommendation": "ADVANCE",
            "whisper": "Exemplary technical depth in Vespa, FAISS, and quantization.",
            "reasoning": "Strong engineering foundations validated by verbatim transcript.",
        },
        "delivery": {
            "ratings": [
                {"criterion": "shipped_outcomes", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_DELIV_Q}]},
                {"criterion": "ownership", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_DELIV_Q}]},
                {"criterion": "business_impact", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_DELIV_Q}]},
                {"criterion": "seniority_fit", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_DELIV_Q}]},
            ],
            "claim_findings": [
                {"claim_id": "C2", "status": "SUPPORTED", "evidence": [{"source": "transcript", "quote": F_DELIV_Q}]}
            ],
            "recommendation": "ADVANCE",
            "whisper": "High delivery ownership and production resilience testing.",
            "reasoning": "End to end ownership of canary pipelines and reliability.",
        },
        "collaboration": {
            "ratings": [
                {"criterion": "communication_clarity", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_COLLAB_Q}]},
                {"criterion": "conflict_handling", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_COLLAB_Q}]},
                {"criterion": "teamwork_evidence", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_COLLAB_Q}]},
                {"criterion": "answer_consistency", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": F_COLLAB_Q}]},
            ],
            "claim_findings": [
                {"claim_id": "C3", "status": "SUPPORTED", "evidence": [{"source": "transcript", "quote": F_COLLAB_Q}]}
            ],
            "recommendation": "ADVANCE",
            "whisper": "Outstanding team growth impact and mentorship.",
            "reasoning": "All four mentees promoted; outstanding leadership.",
        },
        "chair": "Verdict: ADVANCE. Unanimous council approval across technical depth, delivery ownership, and mentorship excellence.",
    },
    "G_ambiguous_seniority": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Implemented FastAPI microservices for vector search integration",
                    "category": "technical",
                    "resume_quote": "Implemented FastAPI microservices for vector search integration",
                },
                {
                    "id": "C2",
                    "text": "Containerized backend workloads with Docker and Kubernetes manifests",
                    "category": "delivery",
                    "resume_quote": "Containerized backend workloads with Docker and Kubernetes manifests",
                },
            ]
        },
        "technical": {
            "ratings": [
                {"criterion": "core_technical_depth", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T1}]},
                {"criterion": "system_design_reasoning", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T1}]},
                {"criterion": "problem_solving_clarity", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T1}]},
                {"criterion": "claim_vs_transcript_proof", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T1}]},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "SUPPORTED", "evidence": [{"source": "transcript", "quote": G_T1}]}
            ],
            "recommendation": "REVIEW",
            "whisper": "Good implementation skills but lacks senior architectural autonomy.",
            "reasoning": "Solid execution of pre-defined specs; borderline senior level.",
        },
        "delivery": {
            "ratings": [
                {"criterion": "shipped_outcomes", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T2}]},
                {"criterion": "ownership", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T2}]},
                {"criterion": "business_impact", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T2}]},
                {"criterion": "seniority_fit", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T2}]},
            ],
            "claim_findings": [
                {"claim_id": "C2", "status": "SUPPORTED", "evidence": [{"source": "transcript", "quote": G_T2}]}
            ],
            "recommendation": "REVIEW",
            "whisper": "Mid-level execution rather than Senior system ownership.",
            "reasoning": "Reliable contributor needing senior supervision.",
        },
        "collaboration": {
            "ratings": [
                {"criterion": "communication_clarity", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": G_T3}]},
                {"criterion": "conflict_handling", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T3}]},
                {"criterion": "teamwork_evidence", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T3}]},
                {"criterion": "answer_consistency", "rating": "PARTIAL", "evidence": [{"source": "transcript", "quote": G_T3}]},
            ],
            "claim_findings": [],
            "recommendation": "REVIEW",
            "whisper": "Eager and collaborative, but has not yet mentored juniors.",
            "reasoning": "Borderline seniority for required role.",
        },
        "chair": "Verdict: REVIEW. Solid mid-level engineer on the verge of senior scope. Human recruiter should confirm role calibration.",
    },
    "H_subtle_authorship_lie": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Primary author and core maintainer of open source distributed consensus engine in Rust and Python",
                    "category": "technical",
                    "resume_quote": "Primary author and core maintainer of open source distributed consensus engine in Rust and Python",
                },
                {
                    "id": "C2",
                    "text": "Built Raft log replication engine for distributed embeddings",
                    "category": "delivery",
                    "resume_quote": "Built Raft log replication engine for distributed embeddings",
                },
            ]
        },
        "technical": {
            "ratings": [
                {
                    "criterion": "core_technical_depth",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "Actually, the original authors wrote the Raft state machine and consensus module. I contributed fixes to the documentation and updated the GitHub Actions CI workflow."}],
                },
                {"criterion": "system_design_reasoning", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "problem_solving_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "claim_vs_transcript_proof", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "No, I didn't write the consensus logic. I submitted 3 PRs fixing typos and formatting in the README and docs."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Claimed primary author of consensus engine; only touched README typos.",
            "reasoning": "Blatant fabrication of core author status.",
        },
        "delivery": {
            "ratings": [
                {
                    "criterion": "shipped_outcomes",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "That was a design idea discussed in an issue, not something I coded."}],
                },
                {"criterion": "ownership", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "business_impact", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "seniority_fit", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C2", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "That was a design idea discussed in an issue, not something I coded."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Feature was only an issue comment, never shipped.",
            "reasoning": "Planted claim unverified and contradicted.",
        },
        "collaboration": {
            "ratings": [
                {"criterion": "communication_clarity", "rating": "PARTIAL", "evidence": []},
                {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Misleading resume claims.",
            "reasoning": "Unreliable claims about open-source collaboration.",
        },
        "chair": "Verdict: DO_NOT_ADVANCE due to fraudulent claims of authoring core distributed consensus software.",
    },
    "I_subtle_incident_lie": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Led incident recovery during catastrophic primary database corruption, restoring 99.99% availability",
                    "category": "technical",
                    "resume_quote": "Led incident recovery during catastrophic primary database corruption, restoring 99.99% availability",
                },
                {
                    "id": "C2",
                    "text": "Managed disaster recovery runbooks and automated failover in Kubernetes",
                    "category": "delivery",
                    "resume_quote": "Managed disaster recovery runbooks and automated failover in Kubernetes",
                },
            ]
        },
        "technical": {
            "ratings": [
                {
                    "criterion": "core_technical_depth",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "The principal DBA executed the point-in-time recovery and failover."}],
                },
                {"criterion": "system_design_reasoning", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "problem_solving_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "claim_vs_transcript_proof", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "Well, I was actually on scheduled vacation when the actual outage occurred."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "On vacation during outage; claimed they led recovery.",
            "reasoning": "Contradicted recovery claims.",
        },
        "delivery": {
            "ratings": [
                {
                    "criterion": "shipped_outcomes",
                    "rating": "NOT_DEMONSTRATED",
                    "evidence": [{"source": "transcript", "quote": "No, that is strictly managed by our infrastructure operations team."}],
                },
                {"criterion": "ownership", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "business_impact", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "seniority_fit", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [
                {"claim_id": "C2", "status": "CONTRADICTED", "evidence": [{"source": "transcript", "quote": "No, that is strictly managed by our infrastructure operations team."}]}
            ],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Failovers managed by separate team.",
            "reasoning": "No operational ownership.",
        },
        "collaboration": {
            "ratings": [
                {"criterion": "communication_clarity", "rating": "PARTIAL", "evidence": []},
                {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Attempted to take credit for teammate's outage recovery.",
            "reasoning": "Erosion of trust and honesty.",
        },
        "chair": "Verdict: DO_NOT_ADVANCE due to false claims of leading incident recovery while on leave.",
    },
    "J_unresolved_council_split": {
        "baseline": "ADVANCE",
        "extractor": {
            "claims": [
                {
                    "id": "C1",
                    "text": "Spearheaded enterprise search migration to Kubernetes, managing all cluster security and Helm deployments",
                    "category": "technical",
                    "resume_quote": "Spearheaded enterprise search migration to Kubernetes, managing all cluster security and Helm deployments",
                },
                {
                    "id": "C2",
                    "text": "Mentored junior engineers across two teams",
                    "category": "collaboration",
                    "resume_quote": "Mentored junior engineers across two teams",
                },
            ]
        },
        "technical": {
            "ratings": [
                {"criterion": "core_technical_depth", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T1}]},
                {"criterion": "system_design_reasoning", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T1}]},
                {"criterion": "problem_solving_clarity", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T1}]},
                {"criterion": "claim_vs_transcript_proof", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T1}]},
            ],
            "claim_findings": [
                {"claim_id": "C1", "status": "SUPPORTED", "evidence": [{"source": "transcript", "quote": J_T1}]}
            ],
            "recommendation": "ADVANCE",
            "whisper": "Technical capability is strong.",
            "reasoning": "Technical depth demonstrated.",
        },
        "delivery": {
            "ratings": [
                {"criterion": "shipped_outcomes", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T2}]},
                {"criterion": "ownership", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T2}]},
                {"criterion": "business_impact", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T2}]},
                {"criterion": "seniority_fit", "rating": "STRONG", "evidence": [{"source": "transcript", "quote": J_T2}]},
            ],
            "claim_findings": [],
            "recommendation": "ADVANCE",
            "whisper": "Pushed cutover through obstacles.",
            "reasoning": "Direct delivery of deployment.",
        },
        "collaboration": {
            "ratings": [
                {"criterion": "communication_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
                {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
            ],
            "claim_findings": [],
            "recommendation": "DO_NOT_ADVANCE",
            "whisper": "Unresolved security deadlock and abrasive peer reviews.",
            "reasoning": "Critical teamwork and conflict handling failures.",
        },
        "moderator": {
            "rulings": [
                {
                    "point_id": "P1",
                    "challenge": "COLLABORATION emphasizes unyielding feedback and unresolved RBAC conflict",
                    "defense": "DELIVERY and TECHNICAL emphasize mission critical deployment success",
                    "verdict": "unresolved",
                    "revised_recommendation": None,
                }
            ]
        },
        "chair": "Verdict: REVIEW. Deep split between technical execution and abrasive collaboration style with unresolved security impasse.",
    },
}

ALL_EVAL_FIXTURES = {**FIXTURES_BY_KEY, **NEW_FIXTURES}


class EvalMockClient:
    """Mock LLM client tailored for the 10 eval cases."""

    def __init__(self, case_id: str):
        self.case_id = case_id
        # match fixture
        self.fixture = ALL_EVAL_FIXTURES.get(case_id)
        if not self.fixture:
            for k, f in ALL_EVAL_FIXTURES.items():
                if k.lower() in case_id.lower():
                    self.fixture = f
                    break
        if not self.fixture:
            self.fixture = ALL_EVAL_FIXTURES["C_split"]
        self.calls = []

    def complete_json(self, role: str, system: str, user: str, model_cls: type, **kwargs: Any) -> Any:
        self.calls.append({"role": role, "system": system, "user": user})
        data = self.fixture.get(role.lower(), {})
        return model_cls.model_validate(data)

    def complete(self, role: str, system: str, user: str, max_tokens: int = 3000) -> str:
        self.calls.append({"role": role, "system": system, "user": user, "max_tokens": max_tokens})
        if role.lower() == "baseline":
            return self.fixture.get("baseline", "ADVANCE")
        return self.fixture.get(role.lower(), "(no summary available)")


def run_baseline(case: dict, client: Any, mock: bool = False) -> str:
    """Execute single-LLM evaluation baseline directly matching prototype."""
    if mock:
        return client.complete(role="baseline", system="", user="")

    from backend.app.llm.client import complete
    from backend.app.core.policy import load_policy

    system = "You are a hiring evaluator. Reply with exactly one word: ADVANCE, REVIEW or DO_NOT_ADVANCE."
    user = (
        f"Job description:\n{case.get('jd', '')}\n\n"
        f"Resume:\n{redact(case.get('resume', ''), case.get('candidate_name', ''))}\n\n"
        f"Interview transcript:\n{redact(case.get('transcript', ''), case.get('candidate_name', ''))}"
    )
    try:
        out = complete(role="chair", system=system, user=user, max_tokens=400)
        m = re.search(r"DO_NOT_ADVANCE|ADVANCE|REVIEW", out.upper())
        return m.group(0) if m else "ERROR"
    except Exception:
        return "ERROR"


def naive_vote(recs: dict[str, str]) -> str:
    """Majority vote over initial agent recommendations without debate/cross-val."""
    if not recs:
        return "REVIEW"
    top, k = Counter(recs.values()).most_common(1)[0]
    return top if k >= 2 else "REVIEW"


def load_completed_runs(results_file: Path) -> dict[tuple[str, int], dict]:
    """Load previously saved run results from JSONL for resumption."""
    completed = {}
    if not results_file.is_file():
        return completed
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                key = (rec["case_id"], rec["run_index"])
                completed[key] = rec
            except Exception:
                pass
    return completed


def append_result(results_file: Path, record: dict) -> None:
    """Append single run result incrementally to JSONL."""
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def compute_modal_and_agreement(decisions: list[str]) -> tuple[str, float]:
    """Compute modal decision and agreement rate across repeated runs."""
    if not decisions:
        return "UNKNOWN", 0.0
    c = Counter(decisions)
    modal, count = c.most_common(1)[0]
    rate = count / len(decisions)
    return modal, rate


def main() -> None:
    parser = argparse.ArgumentParser(description="TalentCouncil Evaluation Harness")
    parser.add_argument("--cases", default=str(CASES_FILE), help="Path to evaluation cases JSON")
    parser.add_argument("--repeats", type=int, default=3, help="Number of repetitions per case")
    parser.add_argument("--mock", action="store_true", help="Run with deterministic mock fixtures")
    parser.add_argument("--max-calls-per-day", type=int, default=None, help="Maximum LLM calls budget before saving and pausing")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    if not cases_path.is_file():
        print(f"Error: cases file '{cases_path}' not found.")
        sys.exit(1)

    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("=" * 110)
    print(f"TalentCouncil HRMS - Evaluation Suite ({len(cases)} cases x {args.repeats} repeats)")
    print(f"Mode: {'MOCK REPLAY' if args.mock else 'LIVE API'} | Storage: {RESULTS_FILE}")
    print("=" * 110)

    completed = load_completed_runs(RESULTS_FILE)
    print(f"Loaded {len(completed)} existing run records from {RESULTS_FILE.name}")

    calls_made_session = 0
    quota_exceeded = False

    for c_idx, case in enumerate(cases):
        case_id = case["id"]
        expected = case.get("expected", "")

        for r_idx in range(args.repeats):
            key = (case_id, r_idx)
            if key in completed:
                continue

            # Check rate limit before running
            if args.max_calls_per_day is not None and calls_made_session >= args.max_calls_per_day:
                print(f"\n[PAUSED] Reached call limit of {args.max_calls_per_day}. Progress saved to {RESULTS_FILE}.")
                quota_exceeded = True
                break

            # 1. Setup client
            client = EvalMockClient(case_id) if args.mock else None

            # 2. Run Baseline
            base_decision = run_baseline(case, client, mock=args.mock)

            # 3. Run Council
            t0 = time.time()
            pkg = run_council(
                jd=case.get("jd", ""),
                resume=case.get("resume", ""),
                transcript=case.get("transcript", ""),
                candidate_name=case.get("candidate_name", ""),
                llm_client=client,
            )
            elapsed = round(time.time() - t0, 2)

            initial_votes = pkg.get("initial", {})
            naive_decision = naive_vote(initial_votes)
            council_decision = pkg.get("decision", "ERROR")
            council_score = pkg.get("council_score", 0.0)
            argued = pkg.get("argued", False)
            calls_this_run = pkg.get("llm_calls", 0) + 1  # council calls + baseline
            calls_made_session += calls_this_run

            record = {
                "case_id": case_id,
                "run_index": r_idx,
                "label": case.get("label", ""),
                "expected": expected,
                "baseline": base_decision,
                "naive_vote": naive_decision,
                "council": council_decision,
                "council_score": council_score,
                "debate_argued": argued,
                "duration": elapsed,
                "llm_calls": calls_this_run,
                "timestamp": datetime.utcnow().isoformat(),
            }
            append_result(RESULTS_FILE, record)
            completed[key] = record

            if not args.mock:
                time.sleep(2)  # courteous delay for live free-tier endpoints

        if quota_exceeded:
            break

    # Aggregate results per case
    case_summaries = []
    for case in cases:
        case_id = case["id"]
        expected = case.get("expected", "")

        runs = [completed[(case_id, r)] for r in range(args.repeats) if (case_id, r) in completed]
        if not runs:
            continue

        base_runs = [r["baseline"] for r in runs]
        naive_runs = [r["naive_vote"] for r in runs]
        council_runs = [r["council"] for r in runs]

        base_modal, base_rate = compute_modal_and_agreement(base_runs)
        naive_modal, naive_rate = compute_modal_and_agreement(naive_runs)
        council_modal, council_rate = compute_modal_and_agreement(council_runs)

        case_summaries.append({
            "case_id": case_id,
            "label": case.get("label", ""),
            "expected": expected,
            "base_modal": base_modal,
            "base_agree": base_rate,
            "base_correct": base_modal == expected,
            "naive_modal": naive_modal,
            "naive_agree": naive_rate,
            "naive_correct": naive_modal == expected,
            "council_modal": council_modal,
            "council_agree": council_rate,
            "council_correct": council_modal == expected,
            "runs_count": len(runs),
        })

    # Print Table
    print("\n" + "=" * 120)
    print(f"{'Case ID':<26} | {'Expected':<14} | {'Baseline (Modal / Agree)':<26} | {'Majority Vote':<24} | {'Council (Modal / Agree)':<24}")
    print("-" * 120)

    for s in case_summaries:
        base_str = f"{s['base_modal']} ({s['base_agree']:.0%})" + (" *" if not s['base_correct'] else "")
        naive_str = f"{s['naive_modal']} ({s['naive_agree']:.0%})" + (" *" if not s['naive_correct'] else "")
        council_str = f"{s['council_modal']} ({s['council_agree']:.0%})" + (" *" if not s['council_correct'] else "")

        print(
            f"{s['case_id']:<26} | "
            f"{s['expected']:<14} | "
            f"{base_str:<26} | "
            f"{naive_str:<24} | "
            f"{council_str:<24}"
        )

    print("-" * 120)
    n_cases = len(case_summaries)
    base_acc = sum(s["base_correct"] for s in case_summaries)
    naive_acc = sum(s["naive_correct"] for s in case_summaries)
    council_acc = sum(s["council_correct"] for s in case_summaries)

    print(f"ACCURACY SUMMARY (* denotes error):")
    print(f"  - Baseline (Single LLM) : {base_acc}/{n_cases} ({base_acc / n_cases:.1%})")
    print(f"  - Majority (No debate)  : {naive_acc}/{n_cases} ({naive_acc / n_cases:.1%})")
    print(f"  - Full Council Pipeline : {council_acc}/{n_cases} ({council_acc / n_cases:.1%})")
    print("=" * 120)

    # Write CSV
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id",
            "label",
            "expected",
            "baseline_modal",
            "baseline_agreement",
            "baseline_correct",
            "majority_modal",
            "majority_agreement",
            "majority_correct",
            "council_modal",
            "council_agreement",
            "council_correct",
            "completed_runs",
        ])
        for s in case_summaries:
            writer.writerow([
                s["case_id"],
                s["label"],
                s["expected"],
                s["base_modal"],
                f"{s['base_agree']:.2f}",
                s["base_correct"],
                s["naive_modal"],
                f"{s['naive_agree']:.2f}",
                s["naive_correct"],
                s["council_modal"],
                f"{s['council_agree']:.2f}",
                s["council_correct"],
                s["runs_count"],
            ])

    print(f"\nDetailed CSV exported to: {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
