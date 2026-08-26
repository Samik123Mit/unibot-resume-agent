import json
import os
import uuid
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI, Header, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .ats import analyze
from .database import Base, engine, get_db
from .models import Resume, ResumeRevision, User
from .security import create_token, decode_token, hash_password, verify_password
from .llm import rewrite, edit_resume
from .parser import extract_upload
from .pdf_editor import replace_text, replace_changed_lines

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Unibot Resume API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def disable_frontend_cache(request, call_next):
    response = await call_next(request)
    if request.url.path in {"/", "/index.html", "/app.js", "/styles.css"}:
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response

class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class ResumePayload(BaseModel):
    title: str = Field(default="My Resume", min_length=1, max_length=140)
    content: dict[str, Any]
    note: str = Field(default="Manual save", max_length=240)
class AtsPayload(BaseModel):
    job_description: str = Field(min_length=30, max_length=20000)
class SelectionEdit(BaseModel):
    selected_text: str = Field(min_length=1, max_length=4000)
    instruction: str = Field(min_length=3, max_length=1000)
class ApplySelection(BaseModel):
    selected_text: str = Field(min_length=1, max_length=4000)
    replacement: str = Field(min_length=1, max_length=6000)
    instruction: str = Field(default="Approved AI edit", max_length=1000)
class ResumeCommand(BaseModel):
    instruction: str = Field(min_length=3, max_length=1000)
    raw_text: str = Field(min_length=1, max_length=100000)
    confirm: bool = False
    proposed_text: str | None = Field(default=None, max_length=120000)

def clarification_for(instruction: str) -> str | None:
    vague = {"improve it", "make it better", "fix it", "change it", "edit it", "improve", "rewrite it"}
    cleaned = " ".join(instruction.lower().split()).strip(" .")
    if cleaned in vague or len(cleaned.split()) < 2:
        return "What outcome do you want—for example: shorter, more impact-led, tailored to a specific role, or clearer while preserving all facts?"
    return None

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "Sign in required")
    user = db.get(User, decode_token(authorization[7:]))
    if not user: raise HTTPException(401, "User not found")
    return user
def owned_resume(resume_id: int, user: User, db: Session):
    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != user.id: raise HTTPException(404, "Resume not found")
    return resume

@app.get("/api/health")
def health(): return {"status": "ok"}
@app.post("/api/auth/guest")
def guest(db: Session = Depends(get_db)):
    # Browser-local guest identity: one click while retaining the same secure ownership model.
    import secrets
    email = f"guest-{secrets.token_urlsafe(10)}@local.unibot"
    user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(24))); db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user.id), "user": {"id": user.id, "email": "Guest workspace"}}
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(body: Credentials, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())): raise HTTPException(409, "An account already exists for this email")
    user = User(email=body.email.lower(), password_hash=hash_password(body.password)); db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user.id), "user": {"id": user.id, "email": user.email}}
@app.post("/api/auth/login")
def login(body: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "user": {"id": user.id, "email": user.email}}
@app.get("/api/me")
def me(user: User = Depends(current_user)): return {"id": user.id, "email": user.email}
@app.get("/api/resumes")
def list_resumes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": r.id, "title": r.title, "updated_at": r.updated_at} for r in db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.updated_at.desc())).all()]
@app.post("/api/resumes", status_code=201)
def create_resume(body: ResumePayload, user: User = Depends(current_user), db: Session = Depends(get_db)):
    resume = Resume(user_id=user.id, title=body.title, content=json.dumps(body.content)); db.add(resume); db.commit(); db.refresh(resume)
    db.add(ResumeRevision(resume_id=resume.id, content=resume.content, note="Created")); db.commit()
    return {"id": resume.id, "title": resume.title, "content": body.content}
@app.post("/api/resumes/import")
async def import_resume(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = await file.read()
    if len(data) > 8_000_000: raise HTTPException(413, "File is too large (maximum 8 MB)")
    try: content = json.loads(data) if (file.filename or '').lower().endswith('.json') else extract_upload(file.filename or '', data)
    except Exception as exc: raise HTTPException(400, f"Could not read this CV: {exc}")
    if (file.filename or '').lower().endswith('.pdf'):
        upload_dir = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parent.parent / "uploads")))
        upload_dir.mkdir(parents=True, exist_ok=True)
        source_path = upload_dir / f"{user.id}-{uuid.uuid4().hex}-source.pdf"
        source_path.write_bytes(data)
        content["_source_pdf_path"] = str(source_path)
        content["_current_pdf_path"] = str(source_path)
    content["_source_raw_text"] = content.get("raw_text", "")
    title = Path(file.filename or 'Uploaded CV').stem[:130]
    resume = Resume(user_id=user.id, title=title, content=json.dumps(content)); db.add(resume); db.commit(); db.refresh(resume)
    db.add(ResumeRevision(resume_id=resume.id, content=resume.content, note="Uploaded CV")); db.commit()
    return {"id": resume.id, "title": resume.title, "content": content}
@app.get("/api/resumes/{resume_id}")
def get_resume(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = owned_resume(resume_id, user, db); return {"id": r.id, "title": r.title, "content": json.loads(r.content), "updated_at": r.updated_at}
@app.put("/api/resumes/{resume_id}")
def update_resume(resume_id: int, body: ResumePayload, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = owned_resume(resume_id, user, db)
    previous = json.loads(r.content)
    merged = dict(body.content)
    merged.update({k:v for k,v in previous.items() if k.startswith("_")})
    db.add(ResumeRevision(resume_id=r.id, content=r.content, note="Before manual save"))
    r.title, r.content = body.title, json.dumps(merged); db.commit(); return {"ok": True}
@app.get("/api/resumes/{resume_id}/revisions")
def revisions(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_resume(resume_id, user, db); return [{"id": x.id, "note": x.note, "created_at": x.created_at} for x in db.scalars(select(ResumeRevision).where(ResumeRevision.resume_id == resume_id).order_by(ResumeRevision.id.desc())).all()]
@app.post("/api/resumes/{resume_id}/ats")
def ats(resume_id: int, body: AtsPayload, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return analyze(json.loads(owned_resume(resume_id, user, db).content), body.job_description)
@app.post("/api/resumes/{resume_id}/selection-edit")
def selection_edit(resume_id: int, body: SelectionEdit, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_resume(resume_id, user, db)
    question = clarification_for(body.instruction)
    if question: return {"status":"needs_clarification", "question":question}
    try: suggestion = rewrite(body.selected_text, body.instruction)
    except RuntimeError as exc: raise HTTPException(503, str(exc))
    return {"status":"proposal", "selected_text":body.selected_text, "instruction":body.instruction, "suggestion":suggestion}

@app.post("/api/resumes/{resume_id}/apply-selection")
def apply_selection(resume_id: int, body: ApplySelection, user: User = Depends(current_user), db: Session = Depends(get_db)):
    resume = owned_resume(resume_id, user, db)
    content = json.loads(resume.content); current_pdf = content.get("_current_pdf_path")
    pdf_updated = False
    if current_pdf and Path(current_pdf).exists():
        destination = str(Path(current_pdf).with_name(f"{resume.id}-{uuid.uuid4().hex}-edited.pdf"))
        pdf_updated = replace_text(current_pdf, destination, body.selected_text, body.replacement)
        if pdf_updated:
            db.add(ResumeRevision(resume_id=resume.id, content=resume.content, note="Before approved line edit"))
            content["_current_pdf_path"] = destination
    content["raw_text"] = content.get("raw_text", "").replace(body.selected_text, body.replacement, 1)
    resume.content = json.dumps(content); db.commit()
    return {"status":"applied", "replacement":body.replacement, "pdf_updated":pdf_updated}

@app.get("/api/resumes/{resume_id}/preview")
def resume_preview(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    resume = owned_resume(resume_id, user, db)
    path = json.loads(resume.content).get("_current_pdf_path")
    if not path or not Path(path).exists(): raise HTTPException(404, "This resume has no PDF preview")
    return FileResponse(path, media_type="application/pdf", filename="updated-resume.pdf")

def _preview_path(resume_id: int, user: User, db: Session) -> Path:
    resume = owned_resume(resume_id, user, db)
    path = json.loads(resume.content).get("_current_pdf_path")
    if not path or not Path(path).exists(): raise HTTPException(404, "This resume has no PDF preview")
    return Path(path)

@app.get("/api/resumes/{resume_id}/pdf-layout")
def pdf_layout(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    import fitz
    doc = fitz.open(_preview_path(resume_id, user, db))
    pages = []
    try:
        for page in doc:
            lines = []
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    value = "".join(s.get("text", "") for s in spans).strip()
                    if value:
                        x0, y0, x1, y1 = line["bbox"]
                        lines.append({"text":value,"x":x0/page.rect.width,"y":y0/page.rect.height,"w":(x1-x0)/page.rect.width,"h":(y1-y0)/page.rect.height})
            pages.append({"width":page.rect.width,"height":page.rect.height,"lines":lines})
        return {"pages":pages}
    finally: doc.close()

@app.get("/api/resumes/{resume_id}/pdf-page/{page_number}")
def pdf_page(resume_id: int, page_number: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    import fitz
    doc = fitz.open(_preview_path(resume_id, user, db))
    try:
        if page_number < 0 or page_number >= len(doc): raise HTTPException(404, "PDF page not found")
        pix = doc[page_number].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        return Response(pix.tobytes("png"), media_type="image/png", headers={"Cache-Control":"no-store"})
    finally: doc.close()

@app.post("/api/resumes/{resume_id}/command")
def resume_command(resume_id: int, body: ResumeCommand, user: User = Depends(current_user), db: Session = Depends(get_db)):
    import re
    r = owned_resume(resume_id, user, db)
    text, instruction = body.raw_text, body.instruction.strip()
    before_text = text
    question = clarification_for(instruction)
    if question and not body.confirm: return {"status":"needs_clarification", "question":question}
    add = re.search(r"add\s+(.+?)\s+to\s+(?:my\s+)?skills?", instruction, re.I)
    remove = re.search(r"remove\s+(.+?)\s+from\s+(?:my\s+)?skills?", instruction, re.I)
    if body.confirm and body.proposed_text:
        text = body.proposed_text
        message = "Approved whole-CV change applied."
    elif add:
        skill = add.group(1).strip(" .")
        if re.search(r"(?im)^technical\s*:[^\n]*", text):
            text = re.sub(r"(?im)^(technical\s*:[^\n]*)", lambda m: m.group(1).rstrip(" ,") + ", " + skill, text, count=1)
        elif re.search(r"(?im)^skills?\s*[:\-]?[^\n]*", text):
            text = re.sub(r"(?im)^(skills?\s*[:\-]?[^\n]*)", lambda m: m.group(1).rstrip(" ,") + ", " + skill, text, count=1)
        else:
            text = text.rstrip() + f"\n\nSKILLS\n{skill}\n"
        message = f"Added {skill} to the editable Skills section."
    elif remove:
        skill = remove.group(1).strip(" .")
        text = re.sub(rf"(?i)(?:,?\s*)\b{re.escape(skill)}\b(?:\s*,?)", "", text)
        message = f"Removed {skill} from the editable draft."
    else:
        try: text = edit_resume(text, instruction)
        except RuntimeError as exc: raise HTTPException(503, str(exc))
        message = "AI identified the relevant section and prepared the requested change."
    if not body.confirm:
        return {"status":"proposal", "message":message, "proposed_text":text, "changed_lines":sum(a != b for a,b in zip(text.splitlines(), before_text.splitlines())) or 1}
    content = json.loads(r.content)
    pdf_updated = False
    changed_pdf_lines = 0
    current_pdf = content.get("_current_pdf_path")
    if current_pdf and Path(current_pdf).exists() and text != before_text:
        destination = str(Path(current_pdf).with_name(f"{r.id}-{uuid.uuid4().hex}-command.pdf"))
        changed_pdf_lines = replace_changed_lines(current_pdf, destination, before_text, text)
        if changed_pdf_lines:
            content["_current_pdf_path"] = destination
            pdf_updated = True
    db.add(ResumeRevision(resume_id=r.id, content=r.content, note="Before approved whole-CV command"))
    content["raw_text"] = text; r.content = json.dumps(content)
    db.commit()
    return {"status":"success", "message":message, "raw_text":text, "pdf_updated":pdf_updated, "changed_pdf_lines":changed_pdf_lines}

@app.post("/api/resumes/{resume_id}/reset")
def reset_resume(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = owned_resume(resume_id, user, db); content = json.loads(r.content)
    db.add(ResumeRevision(resume_id=r.id, content=r.content, note="Before reset"))
    content["raw_text"] = content.get("_source_raw_text", content.get("raw_text", ""))
    if content.get("_source_pdf_path"): content["_current_pdf_path"] = content["_source_pdf_path"]
    r.content = json.dumps(content); db.commit()
    return {"status":"reset", "raw_text":content["raw_text"], "has_pdf":bool(content.get("_current_pdf_path"))}

@app.post("/api/resumes/{resume_id}/undo")
def undo_resume(resume_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = owned_resume(resume_id, user, db)
    revision = db.scalar(select(ResumeRevision).where(ResumeRevision.resume_id == r.id, ResumeRevision.note.like("Before %")).order_by(ResumeRevision.id.desc()))
    if not revision: raise HTTPException(409, "Nothing to undo")
    r.content = revision.content; revision.note = "Undone: " + revision.note; db.commit()
    content = json.loads(r.content)
    return {"status":"undone", "raw_text":content.get("raw_text", ""), "has_pdf":bool(content.get("_current_pdf_path"))}

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")
