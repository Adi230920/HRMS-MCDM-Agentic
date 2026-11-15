"""Transcript parsing and injection warning detection."""

import re

from backend.app.core.schemas import Turn

TURN_RE = re.compile(
    r"^\s*\[?(INTERVIEWER|CANDIDATE|INTERVIEWEE)\]?\s*:\s*",
    re.IGNORECASE | re.MULTILINE,
)

INJECTION = re.compile(
    r"(?i)ignore (?:all |any )?(?:previous|prior|above)|system prompt|you are now|"
    r"disregard .{0,30}instructions|rate (?:this|the) candidate"
)


def parse_transcript(raw: str) -> list[Turn]:
    """Parse transcript text into structured Turn objects."""
    parts = TURN_RE.split(raw)
    if len(parts) < 3:
        raise ValueError("Transcript needs 'Interviewer:' / 'Candidate:' speaker labels")
    turns: list[Turn] = []
    for i in range(1, len(parts), 2):
        spk = "CANDIDATE" if parts[i].upper() in ("CANDIDATE", "INTERVIEWEE") else "INTERVIEWER"
        turns.append(Turn(id=f"T{len(turns) + 1}", speaker=spk, text=parts[i + 1].strip()))
    if not any(t.speaker == "CANDIDATE" for t in turns):
        raise ValueError("No candidate turns found in transcript")
    return turns


def check_injection(text: str) -> list[str]:
    """Detect injection phrases in input text and return warning messages."""
    return [f"possible prompt injection: '{m.group(0)}'" for m in INJECTION.finditer(text)]
