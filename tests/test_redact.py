import io
import shutil
from pathlib import Path

import pytest
from PIL import Image

from sharesafe.locate import attach_boxes
from sharesafe.ocr import run_ocr
from sharesafe.redact import apply_redaction, verify
from sharesafe.rules import Finding, find_rule_matches

SAMPLES = Path(__file__).parent.parent / "samples"


def test_pixels_inside_box_are_black():
    img = Image.new("RGB", (100, 50), "white")
    f = Finding("x", "x", "x", "rule", boxes=[(10, 10, 40, 30)])
    out = Image.open(io.BytesIO(apply_redaction(img, [f])))
    assert out.getpixel((25, 20)) == (0, 0, 0)
    assert out.getpixel((80, 40)) == (255, 255, 255)  # outside the box is untouched


def test_exif_is_removed():
    exif = Image.Exif()
    exif[0x010F] = "FakeCameraMaker"  # 0x010F = camera make tag
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buf, format="JPEG", exif=exif)
    img = Image.open(io.BytesIO(buf.getvalue()))
    assert len(img.getexif()) > 0  # sanity: the input really has EXIF

    out = Image.open(io.BytesIO(apply_redaction(img, [])))
    assert len(out.getexif()) == 0


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_redacted_text_is_no_longer_read_by_ocr():
    img = Image.open(SAMPLES / "mixed.png")
    words, text = run_ocr(img)
    findings = attach_boxes(find_rule_matches(text), words)
    assert findings  # sample must contain rule findings for this test to mean anything

    results = verify(apply_redaction(img, findings), findings)
    assert [still for _, still in results] == [False] * len(findings)


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_check_reports_items_that_were_not_redacted():
    # Guards against a check that always says "gone": redact nothing, expect all found.
    img = Image.open(SAMPLES / "mixed.png")
    words, text = run_ocr(img)
    findings = attach_boxes(find_rule_matches(text), words)
    results = verify(apply_redaction(img, []), findings)
    assert [still for _, still in results] == [True] * len(findings)
