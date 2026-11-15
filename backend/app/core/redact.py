"""PII and sensitive information redaction utilities."""

import re

PII = [
    (r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]"),
    (
        r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|\d{5}[\s-]?\d{5})(?!\w)",
        "[PHONE]",
    ),
    (r"(?i)https?://\S+|\b(?:www\.|linkedin\.com|github\.com)\S*", "[URL]"),
    (r"(?i)\b(?:aged?|dob|born(?: in)?)\b\W{0,3}\d{1,4}(?:[/-]\d{1,4}){0,2}", "[AGE]"),
    (r"(?i)\b(?:he|she)\b", "they"),
    (r"(?i)\b(?:his|hers|her)\b", "their"),
    (r"(?i)\bhim\b", "them"),
    (r"(?i)\b(?:mr|mrs|ms|miss)\.?(?=\s)", ""),
]


def redact(text: str, name: str = "") -> str:
    """Redact PII, names, and gendered pronouns from text."""
    for pat, rep in PII:
        text = re.sub(pat, rep, text)
    for tok in {t for t in name.split() if len(t) > 1}:
        text = re.sub(rf"\b{re.escape(tok)}\b", "[CANDIDATE]", text, flags=re.IGNORECASE)
    return text

