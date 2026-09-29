# ShareSafe

Upload a screenshot or photo of a document. ShareSafe suggests sensitive items
(with a reason for each), you tick the ones to hide, and it paints solid black
boxes into the pixels and gives you a clean PNG to download.

**Design rule:** detection only *suggests* (pattern rules + Claude), a human
*approves*, and plain code *redacts*. Claude sees the OCR text only, never the image.

> **Use made-up documents only.** All sample data is fake (`@example.com`,
> 555-01xx phone numbers, public test card numbers). There are no external
> integrations; the only network call is the optional Claude API request.

## Setup (macOS)

```bash
brew install tesseract
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python make_samples.py            # writes the fake images to samples/
```

Optional, for Claude suggestions (names, addresses, IDs):

```bash
export ANTHROPIC_API_KEY=...          # never commit this
export ANTHROPIC_MODEL=claude-opus-5  # optional; this is the default
```

Without a key the app runs with pattern rules only (email, phone, SSN-like, card numbers).

## Run

```bash
streamlit run app.py
```

## Check it

```bash
pytest -q                          # unit tests; no API calls
python eval.py                     # score rules against samples/expected.json
python eval.py --llm               # same, with Claude (uses API calls)
python check_ocr.py samples/mixed.png   # see raw OCR word boxes + rule hits
```

## Sample inputs (`samples/`)

| File | Purpose |
|---|---|
| `invoice_normal.png` | Normal case: name, email, phone, address, test card |
| `invoice_hard.png` | Hard case: two-line address, `415.555.0198`, order number that looks like an ID, "Miller Street" |
| `mixed.png` | Sensitive and harmless numbers side by side (tracking number, date, total) |
| `invoice_blurry.png` | Blurred copy of the normal invoice; OCR misreads text |
| `no_personal_data.png` | Nothing sensitive; should show the "no guarantee" message |
| `not_an_image.png` | Invalid input; a text file with a `.png` name |

## How it works

| Step | File |
|---|---|
| 1. OCR: image to words with pixel boxes | `sharesafe/ocr.py` |
| 2. Pattern rules (Luhn check for cards) | `sharesafe/rules.py` |
| 3. Claude suggestions from text, as structured JSON | `sharesafe/llm.py` |
| 4. Grounding: drop suggestions not in the OCR text | `sharesafe/llm.py` |
| 5. Merge and map findings back to word boxes | `sharesafe/locate.py` |
| 6. Human review (checkboxes, default unticked) | `app.py` |
| 7. Black boxes, new PNG without EXIF, re-OCR check | `sharesafe/redact.py` |

`sharesafe/pipeline.py` runs steps 1–5 so the app and `eval.py` use identical logic.

## Known limitations

- Blurry or low-resolution images cause OCR misreads, and misread items can be missed.
- The re-OCR check only shows that OCR can no longer read an item, not that a person can't.
- Handwriting, rotated text, and non-English documents are untested.
- Images only (no PDFs).
