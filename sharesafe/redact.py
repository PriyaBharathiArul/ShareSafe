"""Step 7: the only code that changes pixels. Plain, predictable, no AI."""
import io

from PIL import Image, ImageDraw

from sharesafe.locate import match_words
from sharesafe.ocr import run_ocr
from sharesafe.rules import Finding


def apply_redaction(img: Image.Image, approved: list[Finding]) -> bytes:
    # Solid black fill replaces the pixels. A blur or a semi-transparent box
    # could be reversed or read through; opaque black cannot.
    out = img.convert("RGB")
    draw = ImageDraw.Draw(out)
    for f in approved:
        for box in f.boxes:
            draw.rectangle(box, fill=(0, 0, 0))

    # Copy only the raw pixels into a brand-new image, so no metadata (EXIF:
    # camera, GPS location, timestamps) from the original travels with the download.
    clean = Image.frombytes("RGB", out.size, out.tobytes())
    buf = io.BytesIO()
    clean.save(buf, format="PNG")
    return buf.getvalue()


def verify(png_bytes: bytes, approved: list[Finding]) -> list[tuple[Finding, bool]]:
    """Re-read the redacted image and report whether OCR can still find each item.
    This proves OCR can't read it any more; it does not prove a human can't."""
    words, _ = run_ocr(Image.open(io.BytesIO(png_bytes)))
    results = []
    for f in approved:
        aligned, loose = match_words(f.text, words)
        # A loose match only counts if it sits where the item used to be;
        # otherwise the same digits inside some other number would count as a leak.
        in_place = any(_inside(words[i], f.boxes) for i in loose)
        results.append((f, bool(aligned) or in_place))
    return results


def _inside(word, boxes) -> bool:
    cx, cy = word.left + word.width / 2, word.top + word.height / 2
    return any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in boxes)
