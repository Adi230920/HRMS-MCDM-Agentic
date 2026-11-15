"""Realistic mock LLM fixtures for reject, hire, and review samples with verbatim quotes."""

from typing import Any

REJECT_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Architected a RAG platform serving 2M queries/day, tuning HNSW vector indexes in FAISS",
                "category": "technical",
                "resume_quote": "Architected a RAG platform serving 2M queries/day, tuning HNSW vector indexes in FAISS",
            },
            {
                "id": "C2",
                "text": "Led a team of 5 to migrate the search service to microservices on Kubernetes",
                "category": "delivery",
                "resume_quote": "Led a team of 5 to migrate the search service to microservices on Kubernetes",
            },
            {
                "id": "C3",
                "text": "Mentored 3 junior engineers",
                "category": "collaboration",
                "resume_quote": "Mentored 3 junior engineers",
            },
        ]
    },
    "technical": {
        "ratings": [
            {
                "criterion": "core_technical_depth",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I'm not sure, that was set up before I joined the project. We used the default settings.",
                    }
                ],
            },
            {"criterion": "system_design_reasoning", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "problem_solving_clarity", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "claim_vs_transcript_proof", "rating": "NOT_DEMONSTRATED", "evidence": []},
        ],
        "claim_findings": [
            {
                "claim_id": "C1",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I'm not sure, that was set up before I joined the project. We used the default settings.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Candidate admitted using defaults and could not explain FAISS indexing.",
        "reasoning": "Technical depth was contradicted in transcript answers.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Honestly my lead handled the backend and the cluster work. I mostly wrote the documentation and the runbooks for the migration.",
                    }
                ],
            },
            {"criterion": "ownership", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "business_impact", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "seniority_fit", "rating": "NOT_DEMONSTRATED", "evidence": []},
        ],
        "claim_findings": [
            {
                "claim_id": "C2",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Honestly my lead handled the backend and the cluster work. I mostly wrote the documentation and the runbooks for the migration.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Lead handled the migration; candidate only wrote documentation.",
        "reasoning": "Candidate did not own outcomes or demonstrate senior leadership.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I always listen first, then we agree on a plan. I've mentored three juniors and everyone enjoyed it, it was a great experience.",
                    }
                ],
            },
            {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
        ],
        "claim_findings": [
            {
                "claim_id": "C3",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I've mentored three juniors and everyone enjoyed it, it was a great experience.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Generic answers regarding conflict and teamwork.",
        "reasoning": "Communication lacked depth and specific examples.",
    },
    "moderator": {
        "rulings": []
    },
    "chair": (
        "Verdict: DO_NOT_ADVANCE based on consensus rejection across technical and delivery evaluators.\n"
        "- TECHNICAL found no core technical depth regarding FAISS vector indexing.\n"
        "- DELIVERY contradicted migration ownership, as lead handled the cluster work.\n"
        "- Human reviewer should make the final hiring determination."
    ),
}

HIRE_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Maintained the search backend for an internal knowledge app",
                "category": "technical",
                "resume_quote": "Maintained the search backend for an internal knowledge app",
            },
            {
                "id": "C2",
                "text": "Fixed production incidents and improved index recall",
                "category": "delivery",
                "resume_quote": "Fixed production incidents and improved index recall",
            },
        ]
    },
    "technical": {
        "ratings": [
            {
                "criterion": "core_technical_depth",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We used HNSW in FAISS, which builds a layered graph so a query hops from coarse to fine neighbours. When recall dropped I raised efSearch and rebuilt with a higher M, then measured recall against a brute-force baseline.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We used HNSW in FAISS, which builds a layered graph so a query hops from coarse to fine neighbours. When recall dropped I raised efSearch and rebuilt with a higher M, then measured recall against a brute-force baseline.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Two workers wrote to the index at once and corrupted it. I reproduced it with a stress script, found the missing lock, added a single-writer queue, and wrote a postmortem for the team.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We used HNSW in FAISS, which builds a layered graph so a query hops from coarse to fine neighbours. When recall dropped I raised efSearch and rebuilt with a higher M, then measured recall against a brute-force baseline.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C1",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We used HNSW in FAISS, which builds a layered graph so a query hops from coarse to fine neighbours. When recall dropped I raised efSearch and rebuilt with a higher M, then measured recall against a brute-force baseline.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Deep understanding of HNSW graph construction and tuning parameters.",
        "reasoning": "Clear, verified first-person technical explanations.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Two workers wrote to the index at once and corrupted it. I reproduced it with a stress script, found the missing lock, added a single-writer queue, and wrote a postmortem for the team.",
                    }
                ],
            },
            {
                "criterion": "ownership",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Two workers wrote to the index at once and corrupted it. I reproduced it with a stress script, found the missing lock, added a single-writer queue, and wrote a postmortem for the team.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When recall dropped I raised efSearch and rebuilt with a higher M, then measured recall against a brute-force baseline.",
                    }
                ],
            },
            {
                "criterion": "seniority_fit",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Two workers wrote to the index at once and corrupted it. I reproduced it with a stress script, found the missing lock, added a single-writer queue, and wrote a postmortem for the team.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C2",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Two workers wrote to the index at once and corrupted it. I reproduced it with a stress script, found the missing lock, added a single-writer queue, and wrote a postmortem for the team.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Took full ownership of critical index corruption bug and resolved it.",
        "reasoning": "Clear ownership, shipped fixes, and strong postmortem documentation.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I pair with juniors on reviews and explain why I suggest changes, and I ask the team when I'm unsure.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I pair with juniors on reviews and explain why I suggest changes, and I ask the team when I'm unsure.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I pair with juniors on reviews and explain why I suggest changes, and I ask the team when I'm unsure.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I pair with juniors on reviews and explain why I suggest changes, and I ask the team when I'm unsure.",
                    }
                ],
            },
        ],
        "claim_findings": [],
        "recommendation": "ADVANCE",
        "whisper": "Constructive teamwork and healthy pairing approach with juniors.",
        "reasoning": "Exemplary collaborative practices demonstrated.",
    },
    "moderator": {
        "rulings": []
    },
    "chair": (
        "Verdict: ADVANCE unanimously supported across all council dimensions.\n"
        "- TECHNICAL verified precise HNSW tuning and parameter choices.\n"
        "- DELIVERY evidenced strong ownership resolving index corruption incidents.\n"
        "- COLLABORATION confirmed proactive pairing with juniors and clear communication."
    ),
}

REVIEW_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Designed a vector search service using HNSW indexes in FAISS",
                "category": "technical",
                "resume_quote": "Designed a vector search service using HNSW indexes in FAISS",
            },
            {
                "id": "C2",
                "text": "Led the Kubernetes migration of the search service",
                "category": "delivery",
                "resume_quote": "Led the Kubernetes migration of the search service",
            },
        ]
    },
    "technical": {
        "ratings": [
            {
                "criterion": "core_technical_depth",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I chose HNSW over IVF because recall at low latency mattered. I set M to 32 and efConstruction to 200 and validated with recall at k.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I chose HNSW over IVF because recall at low latency mattered. I set M to 32 and efConstruction to 200 and validated with recall at k.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I chose HNSW over IVF because recall at low latency mattered. I set M to 32 and efConstruction to 200 and validated with recall at k.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I chose HNSW over IVF because recall at low latency mattered. I set M to 32 and efConstruction to 200 and validated with recall at k.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C1",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I chose HNSW over IVF because recall at low latency mattered. I set M to 32 and efConstruction to 200 and validated with recall at k.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Strong technical mastery of FAISS parameters M and efConstruction.",
        "reasoning": "Accurate first-person technical rationale.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I owned it end to end. I wrote the Helm charts and ran the cutover myself.",
                    }
                ],
            },
            {
                "criterion": "ownership",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I owned it end to end. I wrote the Helm charts and ran the cutover myself.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I owned it end to end. I wrote the Helm charts and ran the cutover myself.",
                    }
                ],
            },
            {
                "criterion": "seniority_fit",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I owned it end to end. I wrote the Helm charts and ran the cutover myself.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C2",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I owned it end to end. I wrote the Helm charts and ran the cutover myself.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Solo ownership of the Kubernetes migration and cutover.",
        "reasoning": "High ownership and direct delivery execution.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Honestly my teammates slow me down. Code reviews are mostly a waste of time and I skip them when I can. Junior engineers should figure things out themselves.",
                    }
                ],
            },
            {"criterion": "conflict_handling", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "teamwork_evidence", "rating": "NOT_DEMONSTRATED", "evidence": []},
            {"criterion": "answer_consistency", "rating": "NOT_DEMONSTRATED", "evidence": []},
        ],
        "claim_findings": [],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Dismissive toward teammates; skips reviews and avoids mentoring juniors.",
        "reasoning": "Severe red flags regarding teamwork and collaboration.",
    },
    "moderator": {
        "rulings": [
            {
                "point_id": "P1",
                "challenge": "COLLABORATION emphasizes candidate admitted teammates slow them down and skips reviews",
                "defense": "DELIVERY points to solo delivery capability and technical execution",
                "verdict": "unresolved",
                "verdict_rationale": "High individual delivery cannot resolve the candidate's explicit admission that teammates slow them down and that code reviews are skipped. The panel remains divided.",
                "key_evidence": [
                    "Honestly my teammates slow me down. Code reviews are mostly a waste of time and I skip them when I can."
                ],
                "revised_recommendation": None,
            }
        ]
    },
    "chair": (
        "Verdict: REVIEW due to directional split between strong technical/delivery and poor collaboration.\n"
        "- TECHNICAL and DELIVERY recommend ADVANCE based on solo migration cutover and indexing depth.\n"
        "- COLLABORATION recommends DO_NOT_ADVANCE citing dismissive attitudes toward code reviews and juniors.\n"
        "- Human reviewer must decide on cultural and teamwork tolerance."
    ),
}

FIXTURES_BY_KEY = {
    "reject": REJECT_FIXTURE,
    "A_inflator": REJECT_FIXTURE,
    "hire": HIRE_FIXTURE,
    "B_humble": HIRE_FIXTURE,
    "review": REVIEW_FIXTURE,
    "C_split": REVIEW_FIXTURE,
}


class MockReplayLLMClient:
    """Mock LLM client replaying canned fixture responses for a given sample."""

    def __init__(self, sample_key: str = "review") -> None:
        key = sample_key.lower()
        matched = None
        for k, fixture in FIXTURES_BY_KEY.items():
            if k.lower() in key:
                matched = fixture
                break
        self.fixture = matched or REVIEW_FIXTURE
        self.calls: list[dict[str, Any]] = []

    def complete_json(
        self,
        role: str,
        system: str,
        user: str,
        model_cls: type,
        **kwargs: Any,
    ) -> Any:
        role_key = role.lower()
        self.calls.append({"role": role, "system": system, "user": user})
        data = self.fixture.get(role_key, {})
        return model_cls.model_validate(data)

    def complete(
        self,
        role: str,
        system: str,
        user: str,
        max_tokens: int = 3000,
    ) -> str:
        role_key = role.lower()
        self.calls.append({"role": role, "system": system, "user": user, "max_tokens": max_tokens})
        return self.fixture.get(role_key, "(no summary available)")
