from io import BytesIO
import re
from docx import Document
from pypdf import PdfReader

def extract_upload(name: str, data: bytes) -> dict:
    suffix = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if suffix == 'pdf': text = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(data)).pages)
    elif suffix == 'docx': text = '\n'.join(p.text for p in Document(BytesIO(data)).paragraphs)
    elif suffix in {'txt', 'md'}: text = data.decode('utf-8', errors='replace')
    else: raise ValueError('Upload a PDF, DOCX, TXT, or JSON resume.')
    lines = [x.strip(' •\t') for x in text.splitlines() if x.strip()]
    email = next((x for x in lines if re.search(r'[\w.+-]+@[\w.-]+\.\w+', x)), '')
    phone = next((x for x in lines if re.search(r'(\+?\d[\d ()-]{7,}\d)', x)), '')
    name_line = next((x for x in lines[:8] if len(x) < 70 and not re.search(r'@|\d{4}|resume|curriculum', x, re.I)), 'Your Name')
    bullets = [x for x in lines if len(x) > 35][:18]
    return {"personal":{"name":name_line,"email":email,"phone":phone,"location":"","linkedin":"","website":""},"summary":"","raw_text":text,"experiences":[],"educations":[],"skills":[],"projects":[],"_import_note":"The original document is preserved in the viewer. This is extracted text for ATS analysis and AI-assisted edits."}
