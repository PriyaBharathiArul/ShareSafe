"""See what OCR reads and what the rules flag, before the full app exists.
Usage: python check_ocr.py samples/mixed.png"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sharesafe.locate import attach_boxes
from sharesafe.ocr import run_ocr
from sharesafe.rules import find_rule_matches

path = Path(sys.argv[1] if len(sys.argv) > 1 else "samples/mixed.png")
img = Image.open(path)
words, text = run_ocr(img)
findings = attach_boxes(find_rule_matches(text), words)

print(f"{len(words)} words found in {path}\n")
print(f"{'word':<18}{'left':>6}{'top':>6}{'width':>7}{'height':>7}{'conf':>6}  line")
for w in words:
    print(f"{w.text:<18}{w.left:>6}{w.top:>6}{w.width:>7}{w.height:>7}{w.conf:>6.0f}  {w.line_id}")
print("\nText the detectors will read:\n" + text)

print(f"\nRule findings: {len(findings)}")
for n, f in enumerate(findings, 1):
    where = f"{len(f.boxes)} box(es)" if f.boxes else "COULD NOT LOCATE"
    print(f"  [{n}] {f.category:<6} {f.text!r:<28} {where} - {f.reason}")

# Two layers so the difference is visible: thin blue = every word OCR read,
# thick orange + number = something a rule flagged as possibly sensitive.
overlay = img.convert("RGB")
draw = ImageDraw.Draw(overlay)
for w in words:
    draw.rectangle([w.left, w.top, w.left + w.width, w.top + w.height], outline="blue", width=1)
for n, f in enumerate(findings, 1):
    for box in f.boxes:
        draw.rectangle(box, outline="orange", width=3)
        draw.text((box[2] + 4, box[1] - 4), str(n), fill="darkorange", font=ImageFont.load_default(size=22))
out = path.with_name(path.stem + "_ocr_boxes.png")
overlay.save(out)
print(f"\nSaved overlay: {out}")
print("Blue = every word OCR read. Orange + number = rule finding (a suggestion, nothing redacted).")
