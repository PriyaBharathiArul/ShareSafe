"""ShareSafe UI. Flow: upload -> suggestions -> human ticks items -> code redacts.
Run: streamlit run app.py"""
import hashlib
import io
import os

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

from sharesafe.pipeline import detect
from sharesafe.redact import apply_redaction, verify

COLORS = {"rule": (255, 140, 0), "llm": (140, 60, 220)}  # orange = rule, purple = Claude

st.set_page_config(page_title="ShareSafe", layout="wide")
st.title("ShareSafe")
st.caption("Find and black out personal data in a document image before you share it.")
st.warning("Use made-up documents only. This is a prototype.")

# --- Sidebar: Claude is optional so the app still works with no API key.
has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
use_llm = st.sidebar.toggle("Use Claude suggestions", value=has_key, disabled=not has_key)
st.sidebar.caption(
    "Claude reads the OCR text only (never the image) to suggest names, addresses and IDs."
    if has_key else "No ANTHROPIC_API_KEY set: running with pattern rules only."
)

uploaded = st.file_uploader("Upload a screenshot or photo (PNG or JPG)", type=["png", "jpg", "jpeg"])
if not uploaded:
    st.stop()

# --- Reject bad input with a clear message instead of a stack trace.
data = uploaded.getvalue()
try:
    if not data:
        raise ValueError("empty file")
    Image.open(io.BytesIO(data)).verify()  # verify() checks the file is a real image
    # Phone photos store rotation in EXIF; apply it now, because we strip EXIF on output.
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
except Exception:
    st.error("This file could not be read as an image. Please upload a valid PNG or JPG.")
    st.stop()

# --- Run detection once per (image, toggle). Ticking checkboxes reruns the
# script, and we don't want to call the API again on every click.
run_key = hashlib.sha256(data).hexdigest()[:16] + str(use_llm)
if st.session_state.get("run_key") != run_key:
    with st.spinner("Reading the image and looking for sensitive items..."):
        d = detect(img, use_llm)
    st.session_state.update(run_key=run_key, words=d.words, findings=d.findings,
                            llm_warning=d.llm_warning, dropped=d.dropped, result=None)

words = st.session_state["words"]
findings = st.session_state["findings"]

if st.session_state["llm_warning"]:
    st.info(st.session_state["llm_warning"])
if st.session_state["dropped"]:
    st.caption(f"{len(st.session_state['dropped'])} Claude suggestion(s) dropped: text not found in the document.")
if not words:
    st.warning("No text could be read from this image. Try a sharper or larger image.")

# --- Preview: highlights are only suggestions; nothing is redacted yet.
preview = img.convert("RGBA")
layer = Image.new("RGBA", preview.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(layer)
font = ImageFont.load_default(size=20)
for n, f in enumerate(findings, 1):
    color = COLORS[f.source]
    for box in f.boxes:
        draw.rectangle(box, fill=color + (60,), outline=color + (255,), width=3)
        draw.text((box[2] + 4, box[1] - 2), str(n), fill=color + (255,), font=font)
preview = Image.alpha_composite(preview, layer)

left, right = st.columns([3, 2])
left.image(preview, caption="Orange = pattern rule, purple = Claude suggestion", use_container_width=True)

with right:
    if not findings:
        st.info("No items were found. That does not guarantee there is no sensitive data.")
    else:
        st.subheader("Review each suggestion")
        st.caption("Tick the items you want blacked out. Nothing is changed until you click Apply.")
    approved = []
    for n, f in enumerate(findings, 1):
        who = "rule" if f.source == "rule" else "Claude"
        # Default unchecked: every redaction is an explicit human decision.
        if st.checkbox(f"**#{n} {f.category}** · `{f.text}` · {who}", key=f"chk_{run_key}_{n}"):
            approved.append(f)
        st.caption(f.reason)
        if not f.boxes:
            st.warning("Could not locate this on the image. Redact it manually or leave it unticked.")

    if findings and st.button("Apply redaction", type="primary", disabled=not approved):
        png = apply_redaction(img, approved)
        st.session_state["result"] = (png, verify(png, approved), [id(f) for f in approved])

# --- Result. Hidden if the ticks changed since Apply, so it never shows a stale image.
result = st.session_state.get("result")
if result and result[2] == [id(f) for f in approved]:
    png, checks, _ = result
    st.divider()
    st.image(png, caption="Redacted image (a new PNG with no photo metadata)", use_container_width=True)
    st.success("Redacted the items you approved. Review before sharing.")
    not_located = [f for f in approved if not f.boxes]
    if not_located:
        st.error(f"{len(not_located)} approved item(s) could not be located and were NOT redacted.")
    st.markdown("**Re-read check**")
    for f, still_found in checks:
        if f.boxes:
            st.write(("⚠️ OCR can still read " if still_found else "✓ OCR no longer reads ") + f"`{f.text}`")
    st.caption("This check only shows OCR can no longer read the text. Look at the image yourself too.")
    st.download_button("Download redacted PNG", png, file_name="redacted.png", mime="image/png")
