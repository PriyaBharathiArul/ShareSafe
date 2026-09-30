# ShareSafe: Notes

**Intended user:** A support or operations team member who shares document screenshots in chat, tickets or email many times a day.

**Problem:** Today they crop the image or draw over it in a paint tool before sending. It's slow, it's easy to miss one item (e.g. a phone number in a footer), and a highlighter or light blur can leave text readable. The risk is personal data leaving the company by accident.

**First approach:** Pattern rules for fixed-shape data, an OpenAI model for names, addresses and IDs from OCR text, human approval, then code-only redaction.

**Assumption to test:** Suggest + tick is faster and misses less than redacting by hand, and people will read each suggestion rather than tick everything.

## Key decisions
- **The LLM suggests; code redacts.** The model sees OCR text only, never the image, so a wrong answer can't change pixels without a human ticking it.
- **Rules before AI.** Emails, phones, SSNs and cards have fixed shapes, so rules are cheaper, faster and predictable. Cards must also pass the Luhn check, which stops order/tracking numbers being flagged.
- **Grounding check.** Any AI suggestion whose text isn't in the OCR output is dropped. This is how a plausible but invented answer gets caught.
- **Unticked by default.** Every redaction is an explicit human decision.
- **Provider behind one function.** Only `_call_model()` in `llm.py` talks to the AI; switching from Claude to OpenAI changed that function only. Rules, grounding, redaction and tests were unchanged.
- **Alternatives considered:** Sending the image to a vision model — rejected, because it puts the AI near the pixels and makes answers harder to trace to a location. An agent or RAG — not needed for a one-pass extraction task with nothing to look up; a fixed pipeline is easier to test.
- **Decision changed after trying it:** Matching first ran on one long string with spaces removed. On `mixed.png` the SSN `123-45-6789` also matched inside the tracking number `1234 5678 9012 3456`. Matches must now start and end on word edges, and the post-redaction check uses the same shared helper, with tests.

## Test results (rules-only runs shown; AI adds names, addresses, IDs)
| Input | Expected | What happened | How I checked |
|---|---|---|---|
| Normal: `invoice_normal.png` | Name, email, phone, address, card flagged; total and invoice no. not flagged | Rules found email, phone, card; both traps avoided; after redaction OCR could no longer read any item | Answer key (`eval.py`), zoom on downloaded PNG, re-read check |
| Difficult: `invoice_hard.png` | Dotted phone, two-line address, IDs flagged; look-alike order number and "Miller" not flagged | Rules found `415.555.0198`; order number (fails Luhn) and "Miller" avoided | Answer key with trap items |
| Invalid: `not_an_image.png` | Clear error, no crash | "This file could not be read as an image. Please upload a valid PNG or JPG." | Uploaded in the app |

Eval output (`python eval.py`, rules only): found 9, missed 11, traps 0 across 5 sample images. Misses are mostly names, addresses and IDs (the AI's job) and blur. 33 unit tests pass (`pytest -q`, no API calls).

## Tools used
Python, Streamlit, Tesseract (pytesseract), Pillow, OpenAI SDK (structured outputs), pytest, Git.
Built with Claude Code: it drafted much of the code; I set the design rule, reviewed each file, designed the test cases and traps, and pushed back when tests showed bugs (e.g. the SSN/tracking-number match).

**Time spent:** [fill in, e.g. ~4 hours]

## Known limitations
Blurry images lose items to OCR misreads (rules found 1 of 5 on the blurred invoice vs 3 of 5 on the sharp one). The re-OCR check doesn't prove a human can't read an item. Handwriting, rotated text and non-English documents are untested. Images only (no PDFs). US phone formats only.

**Reused work:** No templates. Libraries are listed above. All sample data is made up.
