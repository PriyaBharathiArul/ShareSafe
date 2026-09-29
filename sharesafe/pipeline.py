"""The whole detection flow in one place, so the app and eval.py run identical logic."""
from dataclasses import dataclass

from PIL import Image

from sharesafe.llm import ground, suggest_with_llm
from sharesafe.locate import attach_boxes, merge
from sharesafe.ocr import Word, run_ocr
from sharesafe.rules import Finding, find_rule_matches


@dataclass
class Detection:
    words: list[Word]
    text: str
    findings: list[Finding]      # suggestions only; nothing is redacted here
    llm_warning: str | None
    dropped: list[Finding]       # AI suggestions removed by the grounding check


def detect(img: Image.Image, use_llm: bool) -> Detection:
    words, text = run_ocr(img)                      # 1. pixels -> words + boxes
    rule_findings = find_rule_matches(text)         # 2. fixed-shape patterns
    llm_findings, warning, dropped = [], None, []
    if use_llm:
        llm_findings, warning = suggest_with_llm(text)     # 3. AI model, text only
        llm_findings, dropped = ground(llm_findings, text)  # 4. drop invented text
    findings = attach_boxes(merge(rule_findings, llm_findings), words)  # 5. back to pixels
    return Detection(words, text, findings, warning, dropped)
