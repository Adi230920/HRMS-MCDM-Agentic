# backend_logic.md

Redaction: replace emails, phones, URLs, age cues, and the supplied candidate name with tokens. Convert gendered pronouns to they.

Transcript: split on Interviewer and Candidate labels into turns T1, T2. Reject text without labels. Warn on phrases like ignore previous instructions.

Quote check: lowercase, normalise quotes and whitespace, then require the quote verbatim in the resume or candidate turns. Ignore quotes under eight characters.

Downgrades, each logged:
- STRONG without a verified transcript quote becomes PARTIAL, or NOT_DEMONSTRATED if none verified.
- PARTIAL without any verified quote becomes NOT_DEMONSTRATED.
- SUPPORTED or CONTRADICTED without a verified transcript quote becomes UNVERIFIED.

Score: NOT_DEMONSTRATED 0, PARTIAL 0.5, STRONG 1, averaged over four criteria.
