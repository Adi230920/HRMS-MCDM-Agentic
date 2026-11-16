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

CASE1_PAYMENTS_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Led the migration of the payment reconciliation service from a monolith to Spring Boot microservices",
                "category": "delivery",
                "resume_quote": "Led the migration of the payment reconciliation service from a monolith to Spring Boot microservices",
            },
            {
                "id": "C2",
                "text": "Cut p95 API latency by 40% by adding composite indexes and rewriting slow PostgreSQL queries",
                "category": "technical",
                "resume_quote": "Cut p95 API latency by 40% by adding composite indexes and rewriting slow PostgreSQL queries",
            },
            {
                "id": "C3",
                "text": "Designed an idempotent retry mechanism for failed payment webhooks using Kafka",
                "category": "technical",
                "resume_quote": "Designed an idempotent retry mechanism for failed payment webhooks using Kafka",
            },
            {
                "id": "C4",
                "text": "Mentored 2 interns on code review practices",
                "category": "collaboration",
                "resume_quote": "Mentored 2 interns on code review practices",
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
                        "quote": "I ran EXPLAIN ANALYZE and found a sequential scan on a table with about 40 million rows. I added a composite index on account_id and created_at, and rewrote the query to stop using OFFSET pagination.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "PARTIAL",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "With OFFSET the database still reads and discards all the skipped rows, so deep pages get slower. I switched to keyset pagination using the last seen created_at and id, which keeps each page cost roughly constant.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "PARTIAL",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "The consumer stores processed event ids in a table with a unique constraint, so a retry that arrives twice is ignored.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "PARTIAL",
                "evidence": [],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C2",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I added a composite index on account_id and created_at, and rewrote the query to stop using OFFSET pagination. The p95 dropped to about 540 milliseconds.",
                    }
                ],
            },
            {
                "claim_id": "C3",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Each webhook carries an event id. The consumer stores processed event ids in a table with a unique constraint, so a retry that arrives twice is ignored.",
                    }
                ],
            },
        ],
        "recommendation": "REVIEW",
        "whisper": "Strong keyset pagination and idempotent Kafka consumer design, but junior on overall architecture.",
        "reasoning": "Technical execution on queries and retries is verified; wider design was owned by senior lead.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [],
            },
            {
                "criterion": "ownership",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be fair, a senior engineer designed the service boundaries and ran the rollout. I wrote the data migration scripts and two of the new endpoints, and I helped test the cutover. I wouldn't say I led it.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [],
            },
            {
                "criterion": "seniority_fit",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C1",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be fair, a senior engineer designed the service boundaries and ran the rollout. I wrote the data migration scripts and two of the new endpoints, and I helped test the cutover. I wouldn't say I led it.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Candidate admitted senior lead owned migration; did not lead reconciliation service cutover.",
        "reasoning": "Leadership claim C1 contradicted during interview.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When QA found a rounding bug in refunds, I wrote a failing test first, fixed it, and walked the product manager through the cause so she could update the customer message.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When QA found a rounding bug in refunds, I wrote a failing test first, fixed it, and walked the product manager through the cause so she could update the customer message.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I now add a QA review step for any money-related change.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be fair, a senior engineer designed the service boundaries and ran the rollout.",
                    }
                ],
            },
        ],
        "claim_findings": [],
        "recommendation": "ADVANCE",
        "whisper": "Transparent about contributions and collaborative with QA and product.",
        "reasoning": "Strong, honest cross-functional collaboration and accountability.",
    },
    "moderator": {
        "rulings": [
            {
                "point_id": "P1",
                "challenge": "DELIVERY challenges that candidate inflated leadership claim",
                "defense": "Candidate was honest and executed endpoints and tests under guidance",
                "verdict": "challenger",
                "verdict_rationale": "Claim was contradicted on resume leadership, but technical contributions remain valid.",
                "key_evidence": [
                    "To be fair, a senior engineer designed the service boundaries and ran the rollout. I wrote the data migration scripts and two of the new endpoints, and I helped test the cutover. I wouldn't say I led it."
                ],
                "revised_recommendation": "ADVANCE",
            }
        ]
    },
    "chair": (
        "Verdict: REVIEW. While candidate demonstrated solid database query optimization and Kafka retry mechanics, "
        "the senior migration leadership claim was contradicted in interview, and role ownership is at an intermediate level."
    ),
}

CASE2_DEVOPS_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Architected a multi-region AWS platform with 99.99% uptime using Terraform and Kubernetes",
                "category": "technical",
                "resume_quote": "Architected a multi-region AWS platform with 99.99% uptime using Terraform and Kubernetes",
            },
            {
                "id": "C2",
                "text": "Owned the on-call rotation and reduced incident response time by 60%",
                "category": "delivery",
                "resume_quote": "Owned the on-call rotation and reduced incident response time by 60%",
            },
            {
                "id": "C3",
                "text": "Led a team of 6 engineers",
                "category": "collaboration",
                "resume_quote": "Led a team of 6 engineers",
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
                        "quote": "Terraform keeps the state inside the .tf files themselves, so whoever pulls the repo has the latest state. We never really needed anything beyond that.",
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
                        "quote": "Terraform keeps the state inside the .tf files themselves, so whoever pulls the repo has the latest state. We never really needed anything beyond that.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Fundamentally misunderstood Terraform state and load balancer health checks.",
        "reasoning": "Severe technical contradictions on Terraform and infrastructure fundamentals.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Mostly the senior engineers handled incidents. I watched the dashboards and let them know when something looked red. I did not run any incident myself, but I learned a lot from watching.",
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
                        "quote": "Mostly the senior engineers handled incidents. I watched the dashboards and let them know when something looked red. I did not run any incident myself, but I learned a lot from watching.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Did not own on-call rotation; only watched dashboards as senior engineers ran incidents.",
        "reasoning": "On-call ownership claim was contradicted in interview.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When two engineers disagreed I sat them down over coffee, listened to both sides, and they found a middle ground.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When two engineers disagreed I sat them down over coffee, listened to both sides, and they found a middle ground.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I run a friendly retro every sprint and the feedback has always been positive.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I mentored a group of six on the team and checked in with each of them weekly, so I'd say I led them in spirit.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C3",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I mentored a group of six on the team and checked in with each of them weekly, so I'd say I led them in spirit.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Friendly mediator style but led team only in spirit.",
        "reasoning": "Communication and empathy ratings are strong, but leadership claim was inflated.",
    },
    "moderator": {
        "rulings": [
            {
                "point_id": "P2",
                "challenge": "Candidate fabricated technical and leadership depth despite personable demeanour",
                "defense": "Candidate communicated amicably",
                "verdict": "challenger",
                "verdict_rationale": "High communication cannot salvage widespread fabrication across core technical and operational domains.",
                "key_evidence": [
                    "Terraform keeps the state inside the .tf files themselves, so whoever pulls the repo has the latest state.",
                    "I mentored a group of six on the team and checked in with each of them weekly, so I'd say I led them in spirit."
                ],
                "revised_recommendation": "DO_NOT_ADVANCE",
            }
        ]
    },
    "chair": (
        "Verdict: DO NOT ADVANCE. Fundamental technical misconceptions regarding Terraform state and load balancing, "
        "combined with contradicted claims regarding on-call ownership and engineering leadership."
    ),
}

CASE3_ANALYST_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Built weekly operations dashboards in Power BI for the logistics team",
                "category": "delivery",
                "resume_quote": "Built weekly operations dashboards in Power BI for the logistics team",
            },
            {
                "id": "C2",
                "text": "Wrote SQL reports on delivery delays and warehouse throughput",
                "category": "technical",
                "resume_quote": "Wrote SQL reports on delivery delays and warehouse throughput",
            },
            {
                "id": "C3",
                "text": "Cleaned and reconciled order data from three source systems",
                "category": "technical",
                "resume_quote": "Cleaned and reconciled order data from three source systems",
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
                        "quote": "I joined the orders table to the carrier events table and used a window function with LAG to compute the gap between pickup and first scan.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I pre-aggregated daily totals into a summary table that refreshes overnight, and I added an index on the shipment id. The Power BI dashboard refresh went from roughly four minutes to under twenty seconds.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "About 3 percent of orders mismatched at first. I traced most of them to a time zone difference in one export, fixed the conversion, and agreed with the system owners on a daily check that I review each morning.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I joined the orders table to the carrier events table and used a window function with LAG to compute the gap between pickup and first scan.",
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
                        "quote": "I joined the orders table to the carrier events table and used a window function with LAG to compute the gap between pickup and first scan.",
                    }
                ],
            },
            {
                "claim_id": "C3",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "About 3 percent of orders mismatched at first. I traced most of them to a time zone difference in one export, fixed the conversion, and agreed with the system owners on a daily check that I review each morning.",
                    }
                ],
            },
        ],
        "recommendation": "ADVANCE",
        "whisper": "Strong SQL window function implementation and data pipeline optimization.",
        "reasoning": "Clear, verified SQL query and data reconciliation execution.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Dispatch moved those routes to a different carrier, and late deliveries fell from about 12 percent to 7 percent over two months.",
                    }
                ],
            },
            {
                "criterion": "ownership",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "The Power BI dashboard refresh went from roughly four minutes to under twenty seconds.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Dispatch moved those routes to a different carrier, and late deliveries fell from about 12 percent to 7 percent over two months.",
                    }
                ],
            },
            {
                "criterion": "seniority_fit",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "agreed with the system owners on a daily check that I review each morning.",
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
                        "quote": "The Power BI dashboard refresh went from roughly four minutes to under twenty seconds.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Demonstrated concrete business impact reducing delivery delays from 12% to 7%.",
        "reasoning": "High ownership and proven business results across logistics operations.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I start with the decision they need to make, show one chart, and keep the detail in an appendix. After a review with the dispatch team I added a short summary line at the top because they told me the tables were too dense.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I put both definitions side by side on one chart using last quarter's data, showed that the numbers differed by four points, and we agreed to publish both with clear labels. I documented it on the dashboard's info page.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "After a review with the dispatch team I added a short summary line at the top because they told me the tables were too dense.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I start with the decision they need to make, show one chart, and keep the detail in an appendix.",
                    }
                ],
            },
        ],
        "claim_findings": [],
        "recommendation": "ADVANCE",
        "whisper": "Excellent stakeholder alignment and non-technical communication.",
        "reasoning": "Constructive conflict resolution with finance and warehouse leads, highly collaborative.",
    },
    "moderator": {
        "rulings": []
    },
    "chair": (
        "Verdict: ADVANCE. Outstanding technical competence in SQL optimization, concrete operational impact reducing "
        "late deliveries from 12% to 7%, and exemplary stakeholder conflict resolution."
    ),
}

CASE4_CLOUD_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Architected multi-region active-active database replication across AWS us-east-1 and eu-west-1, achieving p99 sync latency under 95ms",
                "category": "technical",
                "resume_quote": "Architected multi-region active-active database replication across AWS us-east-1 and eu-west-1, achieving p99 sync latency under 95ms",
            },
            {
                "id": "C2",
                "text": "Championed chaos engineering practices, running quarterly GameDay simulations with Chaos Mesh",
                "category": "delivery",
                "resume_quote": "Championed chaos engineering practices, running quarterly GameDay simulations with Chaos Mesh",
            },
            {
                "id": "C3",
                "text": "Mentored 4 mid-level engineers into technical leads",
                "category": "collaboration",
                "resume_quote": "Mentored 4 mid-level engineers into technical leads",
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
                        "quote": "We maintained vector clocks to detect concurrent writes and applied deterministic last-write-wins resolution with nanosecond timestamps. Our measured p99 replication latency stayed under 95 milliseconds even during peak traffic.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Non-critical reads used eventual consistency from the local region, while financial ledger operations used local quorum reads with conditional expressions to prevent double spends during transient network splits.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We chose DynamoDB Global Tables with custom partition keys to prevent hot partitions across shards.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Our measured p99 replication latency stayed under 95 milliseconds even during peak traffic.",
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
                        "quote": "Our measured p99 replication latency stayed under 95 milliseconds even during peak traffic.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Superb low-level distributed systems mastery and multi-region replication depth.",
        "reasoning": "Demonstrated deep, hands-on architectural competence in DynamoDB and distributed data systems.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I fixed it by introducing jittered exponential backoff and circuit breakers with Resilience4j.",
                    }
                ],
            },
            {
                "criterion": "ownership",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "In our first drill, we caught a cascading retry storm in our payment gateway. I fixed it by introducing jittered exponential backoff and circuit breakers with Resilience4j.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We ran dual active regions for high availability.",
                    }
                ],
            },
            {
                "criterion": "seniority_fit",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We used Chaos Mesh in our staging clusters. I injected 30 percent packet loss and induced sudden region failover during simulated peak load.",
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
                        "quote": "We used Chaos Mesh in our staging clusters. I injected 30 percent packet loss and induced sudden region failover during simulated peak load.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Rigorous chaos engineering and proactive production outage prevention.",
        "reasoning": "Proved end-to-end ownership of system resilience and incident prevention.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I ran weekly 1-on-1 architecture pairing sessions where we walked through distributed consensus algorithms like Raft and Paxos.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I stepped back and let each mentee lead an RFC and present it to our architecture review board.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "All four successfully owned major production microservices.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I ran weekly 1-on-1 architecture pairing sessions where we walked through distributed consensus algorithms like Raft and Paxos.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C3",
                "status": "SUPPORTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "All four successfully owned major production microservices.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Exemplary engineering mentorship empowering mentees to lead RFCs.",
        "reasoning": "Constructive, empowering mentorship and clear architectural communication.",
    },
    "moderator": {
        "rulings": []
    },
    "chair": (
        "Verdict: ADVANCE. Outstanding technical architecture in multi-region distributed systems, "
        "rigorous chaos engineering practices, and exemplary engineering mentorship."
    ),
}

CASE5_SECURITY_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Architected and implemented Zero Trust microsegmentation across 250 Kubernetes clusters using Cilium and eBPF",
                "category": "technical",
                "resume_quote": "Architected and implemented Zero Trust microsegmentation across 250 Kubernetes clusters using Cilium and eBPF",
            },
            {
                "id": "C2",
                "text": "Led real-time incident triage and mitigation for critical CVE kernel exploits",
                "category": "delivery",
                "resume_quote": "Led real-time incident triage and mitigation for critical CVE kernel exploits",
            },
            {
                "id": "C3",
                "text": "Directed security awareness and secure coding reviews across 8 product teams",
                "category": "collaboration",
                "resume_quote": "Directed security awareness and secure coding reviews across 8 product teams",
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
                        "quote": "No, I didn't write the eBPF filters. The vendor managed the low-level rules.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Well, honestly, our external security consulting partner gave us the Cilium Helm charts and default network policies.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I opened Jira tickets when developers complained about blocked ports.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "No, I didn't write the eBPF filters. The vendor managed the low-level rules.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C1",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "No, I didn't write the eBPF filters. The vendor managed the low-level rules.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Admitted external vendor configured Cilium; no hands-on eBPF depth.",
        "reasoning": "Core Zero Trust architecture claim directly contradicted by interview transcript.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "They actually performed the installation and cluster rollouts. I mostly monitored the ticket queue and communicated status updates to management.",
                    }
                ],
            },
            {
                "criterion": "ownership",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be completely transparent, that was our core security operations center team. When an alert fired, they handled the forensic analysis and kernel patching. I attended the retrospective meetings to take notes.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "We turned on the default Trivy scanner toggle in GitLab CI.",
                    }
                ],
            },
            {
                "criterion": "seniority_fit",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I mostly monitored the ticket queue and communicated status updates to management.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C2",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be completely transparent, that was our core security operations center team. When an alert fired, they handled the forensic analysis and kernel patching. I attended the retrospective meetings to take notes.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Zero incident leadership demonstrated; passive note-taker only.",
        "reasoning": "Did not lead incident triage or mitigation; third party owned rollouts.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I just escalate directly to their managers. Security isn't negotiable, so I don't spend time debating technical alternatives with developers.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I just escalate directly to their managers. Security isn't negotiable, so I don't spend time debating technical alternatives with developers.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I just escalate directly to their managers.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I just escalate directly to their managers.",
                    }
                ],
            },
        ],
        "claim_findings": [],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Escalates conflicts directly to managers without engaging developers.",
        "reasoning": "Refuses to collaborate constructively on security alternatives.",
    },
    "moderator": {
        "rulings": []
    },
    "chair": (
        "Verdict: DO_NOT_ADVANCE. Core resume claims regarding Zero Trust architecture and incident triage contradicted; "
        "admitted vendor reliance and absence of technical security depth."
    ),
}

CASE6_DATA_FIXTURE = {
    "extractor": {
        "claims": [
            {
                "id": "C1",
                "text": "Designed and deployed an Apache Iceberg lakehouse on AWS EMR processing 18 TB/day with sub-second query pruning",
                "category": "technical",
                "resume_quote": "Designed and deployed an Apache Iceberg lakehouse on AWS EMR processing 18 TB/day with sub-second query pruning",
            },
            {
                "id": "C2",
                "text": "Optimized Spark streaming ingestion pipelines, slashing compute costs by 45% using z-order clustering and compaction",
                "category": "technical",
                "resume_quote": "Optimized Spark streaming ingestion pipelines, slashing compute costs by 45% using z-order clustering and compaction",
            },
            {
                "id": "C3",
                "text": "Drove company-wide data governance and schema evolution across analytics teams",
                "category": "collaboration",
                "resume_quote": "Drove company-wide data governance and schema evolution across analytics teams",
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
                        "quote": "I implemented automated Iceberg compaction jobs running every four hours, sorted the tables with Z-Order clustering on customer_id and event_timestamp, and enabled Bloom filters on high-cardinality keys. Read query latency dropped by 75% and S3 compute costs fell by 45%.",
                    }
                ],
            },
            {
                "criterion": "system_design_reasoning",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Our raw streaming events arrived via Kafka and were written to S3 via Spark Structured Streaming with 1-minute microbatches. Queries were scanning hundreds of thousands of small files.",
                    }
                ],
            },
            {
                "criterion": "problem_solving_clarity",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Iceberg supports full in-place schema evolution with column ID tracking, so column renames and additions don't break existing data.",
                    }
                ],
            },
            {
                "criterion": "claim_vs_transcript_proof",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Read query latency dropped by 75% and S3 compute costs fell by 45%.",
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
                        "quote": "Read query latency dropped by 75% and S3 compute costs fell by 45%.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Outstanding distributed data engineering and Iceberg table optimization.",
        "reasoning": "Superb mastery of streaming lakehouse architecture and query optimization.",
    },
    "delivery": {
        "ratings": [
            {
                "criterion": "shipped_outcomes",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Read query latency dropped by 75% and S3 compute costs fell by 45%.",
                    }
                ],
            },
            {
                "criterion": "ownership",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When downstream BI queries failed due to type mismatches, I added schema enforcement gates in Great Expectations that reject malformed producer events before they enter the silver layer.",
                    }
                ],
            },
            {
                "criterion": "business_impact",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "Read query latency dropped by 75% and S3 compute costs fell by 45%.",
                    }
                ],
            },
            {
                "criterion": "seniority_fit",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "When downstream BI queries failed due to type mismatches, I added schema enforcement gates in Great Expectations that reject malformed producer events before they enter the silver layer.",
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
                        "quote": "Read query latency dropped by 75% and S3 compute costs fell by 45%.",
                    }
                ],
            }
        ],
        "recommendation": "ADVANCE",
        "whisper": "Proven cost reduction and pipeline reliability.",
        "reasoning": "Delivered concrete measurable infrastructure improvements.",
    },
    "collaboration": {
        "ratings": [
            {
                "criterion": "communication_clarity",
                "rating": "PARTIAL",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I don't give advance deprecation warnings because that delays engineering sprints. If their dashboards break, they can inspect our schema registry.",
                    }
                ],
            },
            {
                "criterion": "conflict_handling",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I refused and blocked their IAM permissions without discussion. They escalated to the VP of Engineering, but I don't compromise on architecture boundaries, even if it creates friction with teams.",
                    }
                ],
            },
            {
                "criterion": "teamwork_evidence",
                "rating": "NOT_DEMONSTRATED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be candid, data analysts constantly complain when columns change, but I expect them to adapt their SQL queries.",
                    }
                ],
            },
            {
                "criterion": "answer_consistency",
                "rating": "STRONG",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "I refused and blocked their IAM permissions without discussion.",
                    }
                ],
            },
        ],
        "claim_findings": [
            {
                "claim_id": "C3",
                "status": "CONTRADICTED",
                "evidence": [
                    {
                        "source": "transcript",
                        "quote": "To be candid, data analysts constantly complain when columns change, but I expect them to adapt their SQL queries. I don't give advance deprecation warnings because that delays engineering sprints.",
                    }
                ],
            }
        ],
        "recommendation": "DO_NOT_ADVANCE",
        "whisper": "Severe resistance to cross-functional alignment; unilateral breaking changes without deprecation.",
        "reasoning": "Hostile relationship with downstream analysts and refusal to communicate breaking changes.",
    },
    "moderator": {
        "rulings": []
    },
    "chair": (
        "Verdict: REVIEW. Strong technical mastery in Apache Spark and Iceberg lakehouse optimization, "
        "but significant cross-functional friction and unilateral schema breaks require human recruiter review."
    ),
}

FIXTURES_BY_KEY = {
    "reject": REJECT_FIXTURE,
    "A_inflator": REJECT_FIXTURE,
    "hire": HIRE_FIXTURE,
    "B_humble": HIRE_FIXTURE,
    "review": REVIEW_FIXTURE,
    "C_split": REVIEW_FIXTURE,
    "case1": CASE1_PAYMENTS_FIXTURE,
    "case1_payments": CASE1_PAYMENTS_FIXTURE,
    "payments": CASE1_PAYMENTS_FIXTURE,
    "case2": CASE2_DEVOPS_FIXTURE,
    "case2_devops": CASE2_DEVOPS_FIXTURE,
    "devops": CASE2_DEVOPS_FIXTURE,
    "case3": CASE3_ANALYST_FIXTURE,
    "case3_analyst": CASE3_ANALYST_FIXTURE,
    "analyst": CASE3_ANALYST_FIXTURE,
    "case4": CASE4_CLOUD_FIXTURE,
    "case4_cloud": CASE4_CLOUD_FIXTURE,
    "cloud": CASE4_CLOUD_FIXTURE,
    "case5": CASE5_SECURITY_FIXTURE,
    "case5_security": CASE5_SECURITY_FIXTURE,
    "security": CASE5_SECURITY_FIXTURE,
    "case6": CASE6_DATA_FIXTURE,
    "case6_data": CASE6_DATA_FIXTURE,
    "data": CASE6_DATA_FIXTURE,
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
