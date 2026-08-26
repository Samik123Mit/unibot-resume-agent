from pathlib import Path
from difflib import SequenceMatcher
from itertools import zip_longest
import fitz

def _normalized(value: str) -> str:
    return " ".join(value.split()).strip().casefold()

def _find_rect(page, target: str):
    hits = page.search_for(target.strip())
    if hits:
        return hits[0]
    wanted = _normalized(target)
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            actual = "".join(span.get("text", "") for span in line.get("spans", []))
            candidate = _normalized(actual)
            if candidate == wanted or (len(wanted) > 24 and (candidate in wanted or wanted in candidate)):
                return fitz.Rect(line["bbox"])
    return None

def _font_for_rect(page, rect) -> str:
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if fitz.Rect(span["bbox"]).intersects(rect):
                    name = span.get("font", "").lower()
                    return "hebo" if "bold" in name or span.get("flags", 0) & 16 else "helv"
    return "helv"

def replace_text(source: str, destination: str, selected: str, replacement: str) -> bool:
    """Replace the first exact text occurrence while keeping the rest of the PDF unchanged."""
    doc = fitz.open(source)
    changed = False
    try:
        for page in doc:
            rect = _find_rect(page, selected)
            if not rect:
                continue
            fontname = _font_for_rect(page, rect)
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            fontsize = max(6, min(12, rect.height * 0.72))
            # Expand horizontally for a rewritten line while retaining its original position.
            target = fitz.Rect(rect.x0, rect.y0, min(page.rect.x1 - 18, max(rect.x1, rect.x0 + 360)), rect.y1 + max(3, rect.height * 0.4))
            page.insert_textbox(target, replacement.strip(), fontname=fontname, fontsize=fontsize, color=(0, 0, 0), lineheight=1.05)
            changed = True
            break
        if changed:
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            doc.save(destination, garbage=4, deflate=True)
        return changed
    finally:
        doc.close()

def replace_changed_lines(source: str, destination: str, before: str, after: str) -> int:
    """Apply line-level text changes from a whole-resume command to the PDF."""
    old_lines, new_lines = before.splitlines(), after.splitlines()
    matcher = SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            changes.extend((old, new) for old, new in zip_longest(old_lines[i1:i2], new_lines[j1:j2], fillvalue="") if old.strip())
        elif tag == "delete":
            changes.extend((old, "") for old in old_lines[i1:i2] if old.strip())
    if not changes:
        return 0
    doc = fitz.open(source)
    changed = 0
    try:
        for old, new in changes:
            found = False
            for page in doc:
                rect = _find_rect(page, old)
                if not rect:
                    continue
                fontname = _font_for_rect(page, rect)
                page.add_redact_annot(rect, fill=(1, 1, 1)); page.apply_redactions()
                if new.strip():
                    fontsize = max(5.5, min(11, rect.height * 0.68))
                    target = fitz.Rect(rect.x0, rect.y0, min(page.rect.x1 - 12, max(rect.x1, rect.x0 + 420)), rect.y1 + max(4, rect.height * 0.45))
                    page.insert_textbox(target, new.strip(), fontname=fontname, fontsize=fontsize, color=(0, 0, 0), lineheight=1.0)
                changed += 1; found = True; break
            if not found:
                continue
        if changed:
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            doc.save(destination, garbage=4, deflate=True)
        return changed
    finally:
        doc.close()
