# conflict_rules.md

Rules run in code. Keep at most four points, highest severity first.

High:
- claim_contradicted: one agent SUPPORTED a claim, another CONTRADICTED it.
- seniority_unsupported: a claim with lead, architect, or own wording has no SUPPORTED status. Skip if manager already marked it CONTRADICTED.
- skill_not_demonstrated: technical rates core_technical_depth NOT_DEMONSTRATED while a peer says ADVANCE.

Medium:
- charisma_gap: communication_clarity STRONG but core_technical_depth NOT_DEMONSTRATED.
- directional_split: ADVANCE and DO_NOT_ADVANCE both present.
- ownership_inconsistent: ownership STRONG but answer_consistency NOT_DEMONSTRATED.
- specialist_dissent: any agent score below 0.45 while another says ADVANCE.

Low:
- citation_unearned: an agent had downgrades.

Each point records rule, severity, challenger, challenged, and a detail string naming the evidence. Debate runs once, never per point.
