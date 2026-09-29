"""Score the detection pipeline against a hand-written answer key.
Usage: python eval.py          (rules only, free)
       python eval.py --llm    (rules + OpenAI model; needs OPENAI_API_KEY, costs API calls)
Prints what it measures. Numbers depend on your machine's OCR and the model run."""
import json
import sys
from pathlib import Path

from PIL import Image

from sharesafe.locate import norm
from sharesafe.pipeline import detect

SAMPLES = Path(__file__).parent / "samples"


def score(expected, findings):
    rows, used = [], set()
    for item in expected["should_flag"]:
        want = norm(item["text"])
        # Only same-category findings count: otherwise the email
        # "jane.sample@example.com" would wrongly count as finding the name "Jane Sample".
        same = [f for f in findings if f.category == item["category"]]
        # Full = a finding covers the whole expected text.
        # Partial = a finding covers only part of it (e.g. one address line).
        full = [f for f in same if want in norm(f.text)]
        part = [f for f in same if norm(f.text) in want and len(norm(f.text)) >= 3]
        hit = full or part
        used.update(id(f) for f in hit)
        status = "found" if full else "partial" if part else "MISSED"
        located = "" if not hit else ("located" if all(f.boxes for f in hit) else "NOT LOCATED")
        rows.append((status, located, item["category"], item["text"]))

    # Anything suggested that isn't in the answer key is a wrong flag, i.e.
    # extra work for the reviewer.
    extras = [f for f in findings if id(f) not in used]
    traps = []
    for t in expected["must_not_flag"]:
        hit = any(norm(t["text"]) in norm(f.text) and t.get("category") in (None, f.category) for f in findings)
        traps.append(("TRAP HIT" if hit else "avoided", t["text"] + (f" as {t['category']}" if "category" in t else "")))
    return rows, extras, traps


def main():
    use_llm = "--llm" in sys.argv
    key = json.loads((SAMPLES / "expected.json").read_text())
    totals = {"found": 0, "partial": 0, "MISSED": 0, "extra": 0, "trap": 0, "unlocated": 0}

    print(f"Mode: {'rules + AI (OpenAI)' if use_llm else 'rules only'}\n")
    for name, expected in key.items():
        if name.startswith("_"):
            continue
        d = detect(Image.open(SAMPLES / name), use_llm)
        rows, extras, traps = score(expected, d.findings)

        print(f"== {name}")
        if d.llm_warning:
            print(f"   note: {d.llm_warning}")
        if d.dropped:
            print(f"   grounding dropped {len(d.dropped)} AI suggestion(s): {[f.text for f in d.dropped]}")
        for status, located, cat, text in rows:
            print(f"   {status:<8}{located:<13}{cat:<11}{text}")
            totals[status] += 1
            totals["unlocated"] += located == "NOT LOCATED"
        for f in extras:
            print(f"   {'EXTRA':<21}{f.category:<11}{f.text}   ({f.source})")
        for status, text in traps:
            print(f"   {status:<21}{'trap':<11}{text}")
            totals["trap"] += status == "TRAP HIT"
        totals["extra"] += len(extras)
        print()

    print("Totals:", ", ".join(f"{k}={v}" for k, v in totals.items()))


if __name__ == "__main__":
    main()
