"""Step 1: turn pixels into words that each know where they sit on the image."""
from dataclasses import dataclass

import pytesseract
from PIL import Image


@dataclass
class Word:
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: float
    # (block, paragraph, line) from Tesseract. Lets us draw one box per line
    # when a finding wraps, e.g. a two-line address.
    line_id: tuple


def run_ocr(img: Image.Image) -> tuple[list[Word], str]:
    """Return positioned words plus one plain-text string built from them."""
    # RGB avoids Tesseract quirks with palette/alpha PNGs from screenshots.
    data = pytesseract.image_to_data(img.convert("RGB"), output_type=pytesseract.Output.DICT)

    words = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        # conf == -1 marks layout rows (blocks/lines), not real words.
        if not text or float(data["conf"][i]) < 0:
            continue
        words.append(Word(
            text=text,
            left=data["left"][i], top=data["top"][i],
            width=data["width"][i], height=data["height"][i],
            conf=float(data["conf"][i]),
            line_id=(data["block_num"][i], data["par_num"][i], data["line_num"][i]),
        ))

    # Rules and the LLM both read this exact string, so both detectors see the
    # same input and every finding can be traced back to these words.
    lines: dict[tuple, list[str]] = {}
    for w in words:
        lines.setdefault(w.line_id, []).append(w.text)
    full_text = "\n".join(" ".join(ws) for ws in lines.values())
    return words, full_text
