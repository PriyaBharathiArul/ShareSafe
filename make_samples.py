"""Generate FAKE test documents. Every value is made up on purpose:
@example.com emails, 555-01xx phone numbers (reserved for fiction), and the
public Visa test card 4111 1111 1111 1111."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent / "samples"


def font(size):
    # A real TrueType font gives OCR a fair chance; fall back so the script
    # still runs on machines without Arial.
    for path in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def render(lines, title):
    img = Image.new("RGB", (900, 120 + 44 * len(lines)), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 30), title, fill="black", font=font(34))
    for i, line in enumerate(lines):
        d.text((40, 100 + 44 * i), line, fill="black", font=font(24))
    return img


NORMAL = [
    "Bill to: Jane Sample",
    "Email: jane.sample@example.com",
    "Phone: (206) 555-0142",
    "Address: 42 Test Lane, Faketown, WA 98000",
    "Card: 4111 1111 1111 1111",
    "Amount due: $120.00",
]

# Hard on purpose: dotted phone, an address that wraps to a second line,
# an order number shaped like an account number, and "Miller Street",
# which a model might wrongly treat as a person's name.
HARD = [
    "Customer: Robert Placeholder   Employee ID: EMP-00417",
    "Ship to: 1200 Miller Street, Suite 5B",
    "Springfield, OR 97000",
    "Call 415.555.0198 with questions",
    "Order number: 4000-1234-5678",
    "Account No. ACCT-889120",
]

NO_PII = [
    "Office closed Monday for maintenance.",
    "Please submit timesheets by Friday.",
    "The cafeteria menu has been updated.",
    "Thank you for your patience.",
]


# Sensitive and harmless lines side by side, including harmless numbers
# (date, total, a tracking code that fails Luhn) that must NOT be flagged.
MIXED = [
    "Team update - 2026-09-29",
    "The quarterly review moved to Thursday at 3pm.",
    "Contact: Alex Example, alex.example@example.com",
    "Direct line 312-555-0177, office total $4,250.00",
    "Tracking: 1234 5678 9012 3456 (not a card)",
    "Payment card on file: 5555 5555 5555 4444",
    "SSN on form: 123-45-6789",
    "Lunch will be provided. Thanks everyone!",
]


def main():
    OUT.mkdir(exist_ok=True)
    render(NORMAL, "INVOICE #1001").save(OUT / "invoice_normal.png")
    render(HARD, "PACKING SLIP").save(OUT / "invoice_hard.png")
    render(NO_PII, "NOTICE").save(OUT / "no_personal_data.png")
    render(MIXED, "MEMO").save(OUT / "mixed.png")
    # Blur simulates a shaky phone photo, where OCR starts to misread.
    render(NORMAL, "INVOICE #1001").filter(ImageFilter.GaussianBlur(2.2)).save(OUT / "invoice_blurry.png")
    # Not an image at all: checks that the app rejects bad uploads clearly.
    (OUT / "not_an_image.png").write_text("this is plain text, not a PNG")
    print(f"Wrote samples to {OUT}")


if __name__ == "__main__":
    main()
