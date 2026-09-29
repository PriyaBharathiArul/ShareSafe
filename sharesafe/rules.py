"""Step 2: deterministic rules for patterns that have a fixed shape.
Rules are predictable and free, so they handle everything a regex can;
the LLM is only used for things regex can't (names, addresses, IDs)."""
import re
from dataclasses import dataclass, field


@dataclass
class Finding:
    text: str          # exact text as it appears in the OCR output
    category: str
    reason: str        # shown to the human so they can judge each suggestion
    source: str        # "rule" or "llm", so the reviewer knows who suggested it
    boxes: list = field(default_factory=list)  # filled in later by locate.py


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Covers (415) 555-0198, 415-555-0198, 415.555.0198, 415 555 0198, +1 prefix.
# (?<!\d) / (?!\d) stop us from matching a slice of a longer number.
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)\s?|\d{3}[\s.-])\d{3}[\s.-]\d{4}(?!\d)")

SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")

# 13-19 digits with optional single spaces/dashes. Many numbers look like
# this (order numbers, tracking codes), so every match must also pass Luhn.
CARD = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")


def luhn_ok(number: str) -> bool:
    """Card numbers carry a checksum digit; random digit strings usually fail it."""
    digits = [int(c) for c in number if c.isdigit()]
    total = 0
    # Double every second digit from the right; subtract 9 if it goes over 9.
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def find_rule_matches(text: str) -> list[Finding]:
    findings = []
    for m in EMAIL.finditer(text):
        findings.append(Finding(m.group(), "email", "Matches the pattern of an email address", "rule"))
    for m in PHONE.finditer(text):
        findings.append(Finding(m.group(), "phone", "Matches a US phone number format", "rule"))
    for m in SSN.finditer(text):
        findings.append(Finding(m.group(), "ssn", "Matches the NNN-NN-NNNN format used by Social Security numbers", "rule"))
    for m in CARD.finditer(text):
        if luhn_ok(m.group()):
            findings.append(Finding(m.group(), "card", "13-19 digits that pass the Luhn checksum used by payment cards", "rule"))
    return findings
