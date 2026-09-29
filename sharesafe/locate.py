"""Step 5: merge findings and map each one back to pixel boxes.
Detectors work on text; redaction works on pixels. This file is the bridge."""
import re

from sharesafe.ocr import Word
from sharesafe.rules import Finding

PAD = 3  # a few extra pixels so box edges don't leave letter fragments visible


def norm(s: str) -> str:
    # Letters and digits only: OCR may split "415.555.0198" into pieces or glue
    # a comma onto "Street,", so punctuation and spacing can't be trusted.
    return re.sub(r"[^a-z0-9]", "", s.lower())


def merge(rule: list[Finding], llm: list[Finding]) -> list[Finding]:
    """Rules win on duplicates because they are deterministic and explainable."""
    seen = {norm(f.text) for f in rule}
    return rule + [f for f in llm if norm(f.text) not in seen]


def match_words(text: str, words: list[Word]) -> tuple[set[int], set[int]]:
    """Return (aligned, loose): indexes of words that contain `text`.
    Shared by locate and by the post-redaction check so both agree on what a match is."""
    # One long normalized string of all words, remembering which word each
    # character came from. Matching on this survives OCR splitting or merging tokens.
    chars, owner, starts, ends = [], [], set(), set()
    for i, w in enumerate(words):
        starts.add(len(chars))
        for c in norm(w.text):
            chars.append(c)
            owner.append(i)
        ends.add(len(chars))
    haystack, needle = "".join(chars), norm(text)

    # Find every occurrence: the same email may appear twice on a page.
    spans, s = [], (haystack.find(needle) if needle else -1)
    while s != -1:
        spans.append((s, s + len(needle)))
        s = haystack.find(needle, s + 1)
    # "Aligned" = starts and ends on word edges. Without this, SSN "123-45-6789"
    # also matched inside tracking number "1234 5678 9012". "Loose" matches are
    # kept for when OCR glues text on, e.g. "Email:jane@...".
    aligned = {i for a, b in spans if a in starts and b in ends for i in owner[a:b]}
    loose = {i for a, b in spans for i in owner[a:b]}
    return aligned, loose


def attach_boxes(findings: list[Finding], words: list[Word]) -> list[Finding]:
    for f in findings:
        aligned, loose = match_words(f.text, words)
        hit_words = aligned or loose  # loose only when there is no clean match

        # One box per text line, so a two-line address gets two tight boxes
        # instead of one big box covering everything between them.
        by_line: dict[tuple, list[Word]] = {}
        for i in sorted(hit_words):
            by_line.setdefault(words[i].line_id, []).append(words[i])
        f.boxes = [
            (min(w.left for w in ws) - PAD, min(w.top for w in ws) - PAD,
             max(w.left + w.width for w in ws) + PAD, max(w.top + w.height for w in ws) + PAD)
            for ws in by_line.values()
        ]
        # f.boxes == [] means "could not locate"; the UI must say so, never hide it.
    return findings
