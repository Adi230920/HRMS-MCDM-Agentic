# frontend.md

Next.js, TypeScript, Tailwind, shadcn/ui. API base URL comes from env.

Screens:
- New evaluation: job description, resume, and transcript fields, optional name for redaction, sample loader, validation, Run button.
- Live run: stage timeline from SSE events, with duration and LLM call count.
- Result: verdict card, three agent cards, claims table, conflict and debate panel, chair summary, audit panel.
- History: list of past runs.

Result must show: decision, council score, AAR, veto badge, a banner stating human decision required, and Verified or Unverified badges on quotes.

Show decisions as text plus icon plus colour. Display redacted text only.
Disable Run while a run is active. Show errors inline.
