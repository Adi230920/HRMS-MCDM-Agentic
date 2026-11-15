# gate_logic.md

All values come from policy.yaml.

Agent recommendation from score: 0.60 or above ADVANCE; below 0.30 DO_NOT_ADVANCE; otherwise REVIEW. Ignore model recommendations.

Order:
- Quorum: two of three agents share a direction, else REVIEW.
- Veto: two or more signals fire. Signals are contradicted claim, technical score below 0.35, manager score below 0.35. Veto lifts ADVANCE to REVIEW, never the reverse.
- ADVANCE needs all agents ADVANCE and zero unresolved points, else REVIEW.

Council score: weighted agent score, weights 0.40, 0.35, 0.25, renormalised over live agents. Multiply by 0.85 per unresolved point and 0.80 per failed agent.

Outlier: agent alone against the others, or one that lost a debated point. AAR: share of agents matching the decision.
