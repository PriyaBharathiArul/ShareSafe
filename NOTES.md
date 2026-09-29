# ShareSafe: Notes (fill in the [brackets])

**Intended user:** [e.g. an operations or claims team member who shares document screenshots in chat or tickets]

**Problem:** [What they do today, e.g. crop or scribble over screenshots by hand, and what goes wrong]

**First approach:** Pattern rules for fixed-shape data, an OpenAI model for names, addresses and IDs from OCR text, human approval, then code-only redaction.

**Assumption to test:** [e.g. "Suggest + tick is faster and misses less than redacting by hand"]

## Key decisions
- **Provider behind one function.** Only `_call_model()` in `llm.py` talks to the AI; switched from Claude to OpenAI by changing that function, env vars, and labels. Rules, grounding, redaction, and tests were unchanged.
- **The LLM suggests; code redacts.** The AI model never sees or edits the image, so a wrong answer can't change pixels without a human ticking it.
- **Rules before AI.** Emails, phones, SSNs and cards have fixed shapes, so rules are cheaper, faster and predictable. Cards must also pass the Luhn check, which stops order numbers being flagged.
- **Grounding check.** Any AI suggestion whose text isn't in the OCR output is dropped. This is how a plausible but invented answer gets caught.
- **Unticked by default.** Every redaction is an explicit human decision.
- **Alternative considered:** [e.g. sending the image to a vision model. Rejected because ... / an agent or RAG. Not needed for a one-pass extraction task because ...]
- **Decision changed after trying it:** Matching first ran on one long string with spaces removed. On `mixed.png` the SSN `123-45-6789` also matched inside the tracking number `1234 5678 9012 3456`. Matches must now start and end on word edges, and the post-redaction check uses the same logic.

## Test results (run these yourself)
| Input | Expected | What happened | How I checked |
|---|---|---|---|
| Normal: [file] | [ ] | [ ] | [ ] |
| Difficult: [file] | [ ] | [ ] | [ ] |
| Invalid: `not_an_image.png` | [ ] | [ ] | [ ] |

Eval output (`python eval.py` / `--llm`): [paste totals]

## Tools used
Python, Streamlit, Tesseract (pytesseract), Pillow, OpenAI SDK (structured outputs), pytest, Git.
Built with Claude Code: [say where it helped, and what you checked or changed].

**Time spent:** [ ]

## Known limitations
Blurry images lose items to OCR misreads. The re-OCR check doesn't prove a human can't read an item. Handwriting, rotated text and non-English documents are untested. Images only. [add your own]

**Reused work:** No templates. Libraries are listed above.
