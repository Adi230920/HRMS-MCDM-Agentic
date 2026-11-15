# prd.md

Product: HiringCouncil, hiring decision support.

Problem: Resume claims go unchecked against interview evidence. One evaluator, human or LLM, gets swayed by buzzwords and gives inconsistent verdicts with no audit trail.

Users: recruiter, hiring auditor, demo examiner.

Goals:
- Verify resume claims against transcript quotes.
- Show agent disagreement and how it resolved.
- Output ADVANCE, REVIEW, or DO_NOT_ADVANCE for a human to confirm.
- Store every run for replay.
- Redact personal data before any model sees it.

Non-goals: auto-rejection, candidate ranking, ATS integration, accounts, production scale.

Success: three samples reach expected decisions, runs finish under 120 seconds, at most seven LLM calls per run, replay is identical, no raw PII stored.
