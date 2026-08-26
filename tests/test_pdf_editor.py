import fitz
from app.pdf_editor import replace_text, replace_changed_lines

def test_selected_text_is_replaced_in_pdf(tmp_path):
    source = tmp_path / "source.pdf"
    revised = tmp_path / "revised.pdf"
    doc = fitz.open(); page = doc.new_page(); page.insert_text((72, 72), "Built slow Python APIs."); doc.save(source); doc.close()
    assert replace_text(str(source), str(revised), "Built slow Python APIs.", "Built fast Python APIs.")
    output = fitz.open(revised)
    text = "".join(page.get_text() for page in output)
    output.close()
    assert "Built fast Python APIs." in text
    assert "Built slow Python APIs." not in text

def test_whole_cv_line_change_updates_pdf(tmp_path):
    source, revised = tmp_path / "skills.pdf", tmp_path / "skills-updated.pdf"
    doc = fitz.open(); page = doc.new_page(); page.insert_text((72, 72), "Technical: Python, SQL"); doc.save(source); doc.close()
    count = replace_changed_lines(str(source), str(revised), "SKILLS\nTechnical: Python, SQL", "SKILLS\nTechnical: Python, SQL, PostgreSQL")
    assert count == 1
    output = fitz.open(revised); text = "".join(page.get_text() for page in output); output.close()
    assert "PostgreSQL" in text

def test_replacement_preserves_bold_style(tmp_path):
    source, revised = tmp_path / "bold.pdf", tmp_path / "bold-updated.pdf"
    doc = fitz.open(); page = doc.new_page(); page.insert_text((72, 72), "SKILLS", fontname="hebo"); doc.save(source); doc.close()
    assert replace_text(str(source), str(revised), "SKILLS", "TECHNICAL SKILLS")
    output = fitz.open(revised)
    fonts = [span["font"] for block in output[0].get_text("dict")["blocks"] for line in block.get("lines", []) for span in line.get("spans", [])]
    output.close()
    assert any("Bold" in font for font in fonts)
