# agent_schema.md

Every evaluating agent returns the same JSON.

Fields:
- ratings: four items with criterion, rating, evidence.
- claim_findings: one per claim id with status and evidence.
- recommendation: advisory only, recomputed in code.
- whisper: alert for peers, maximum 30 words.
- reasoning: maximum 100 words.

Ratings: NOT_DEMONSTRATED, PARTIAL, STRONG.
Statuses: SUPPORTED, CONTRADICTED, UNVERIFIED.
Evidence: source (resume or transcript) and a verbatim quote.

Citations: PARTIAL needs one verified quote. STRONG needs a verified quote from a candidate turn. SUPPORTED and CONTRADICTED need a verified transcript quote.

Code names: technical_evaluator is TECHNICAL, manager is DELIVERY, hr_agent is COLLABORATION. Unknown criteria are ignored. Return raw JSON only, no markdown fences.
