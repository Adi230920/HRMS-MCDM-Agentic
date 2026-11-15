# support_roles.md

Extractor (agents/extractor.py)
- Input: redacted resume.
- Output: up to eight claims with id, text, category, and resume_quote.
- Category is technical, delivery, or collaboration.
- Drop any claim whose quote is not verbatim in the resume.

Moderator (agents/moderator.py)
- Input: all contested points with both agents' evidence.
- One batched call. Mandate is adversarial, not conciliatory.
- Per point: challenge, defense, and verdict of challenger, challenged, or unresolved.
- Unresolved is valid. Never force a resolution.
- Set revised_recommendation only for the losing agent, only if evidence changes its direction.
- Skip the call when no points exist.

Both return Pydantic-validated JSON. Failures return an empty result, never an exception.
