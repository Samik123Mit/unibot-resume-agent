# Unibot Resume Agent

Unibot is an AI-assisted placement-CV studio that imports an existing resume, preserves its PDF appearance, evaluates job relevance transparently, proposes contextual edits, and regenerates an approved PDF revision.

> Live application: **[https://unibot-resume-agent.onrender.com](https://unibot-resume-agent.onrender.com)**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Samik123Mit/unibot-resume-agent)

## Product capabilities

- One-click guest workspace plus JWT registration/login APIs.
- PDF, DOCX, TXT, and JSON resume import.
- Exact PDF-page rendering with selectable text overlays.
- Whole-line click selection or character-level drag selection.
- Local Ollama development model or any OpenAI-compatible hosted model.
- Clarifying questions for vague prompts.
- Proposal-first workflow: AI suggestions never alter the source until explicitly approved.
- PDF replacement that preserves bold styling where detected.
- Whole-CV commands such as `Add PostgreSQL to skills` with section routing.
- Download, undo, reset-to-original, and revision history.
- Transparent ATS-readiness formula with BM25 relevance, evidence quality, and structural checks.
- ATS missing-term suggestions staged for review before any source-PDF update.
- Multi-tenant SQL persistence: SQLite locally and PostgreSQL in production.

## ATS methodology

No universal “ATS score” exists because hiring platforms use proprietary parsers and ranking configurations. Unibot reports a reproducible **ATS-readiness estimate**:

| Component | Weight | Purpose |
|---|---:|---|
| BM25 job relevance | 70% | Saturated term relevance between the CV and job description |
| Evidence quality | 20% | Action-led and quantified achievement lines |
| Resume structure | 10% | Presence of education, experience, skills, and projects |

The relevance component follows Robertson and Zaragoza’s BM25 framework. Occupation and skills terminology references the U.S. Department of Labor-sponsored O*NET content model. These sources are also linked inside every UI report.

- [The Probabilistic Relevance Framework: BM25 and Beyond](https://doi.org/10.1561/1500000019)
- [O*NET Content Model](https://www.onetcenter.org/content.html)

## Architecture

```mermaid
flowchart LR
    B[Browser CV Studio] -->|JWT + JSON/multipart| API[FastAPI]
    API --> DB[(PostgreSQL)]
    API --> FS[(Persistent PDF storage)]
    API --> AI[Ollama locally / hosted LLM]
    API --> ATS[BM25 + evidence analyzer]
    API --> PDF[PyMuPDF revision engine]
    PDF --> FS
    FS --> B
```

Detailed architecture, security boundaries, state transitions, and failure modes are documented in [docs/MASTER_DOCUMENT.md](docs/MASTER_DOCUMENT.md).

## Prototype Multi-Agent Architecture

The repository also contains a separate **prototype multi-agent resume-editing layer**. This is useful to discuss in interviews, but it is **not the runtime currently wired into the deployed FastAPI app**.

```mermaid
flowchart TD
    U[User Request] --> A[Root Agent<br/>agent.py]
    A -->|resume edit request| R[Resume Manager Agent<br/>resume_agent.py]
    A -->|general career question| G[Direct response]
    R --> S1[Summary Agent<br/>summary_agent.py]
    R --> S2[Experiences Agent<br/>experiences_agent.py]
    R --> S3[Educations Agent<br/>educations_agent.py]
    R --> S4[Skills Agent<br/>skills_agent.py]
    R --> S5[Projects Agent<br/>projects_agent.py]
    S1 --> RT[Read Tools<br/>read_tools.py]
    S2 --> RT
    S3 --> RT
    S4 --> RT
    S5 --> RT
    S1 --> WT[Write Tools<br/>write_tools.py]
    S2 --> WT
    S3 --> WT
    S4 --> WT
    S5 --> WT
    RT --> RS[Shared Resume State<br/>resume_state.py + resume_data.json]
    WT --> RS
```

### How the agent hierarchy is intended to work

- **Root agent**: [agent.py](agent.py)
  - Entry point for the Google ADK-style assistant.
  - Handles broad career questions directly.
  - Delegates resume-editing requests to the resume manager agent.

- **Resume manager agent**: [resume_agent.py](resume_agent.py)
  - Acts as the router for resume-specific requests.
  - Decides whether the user wants to edit the summary, experience, education, skills, or projects.
  - Delegates the task to the correct section agent.

- **Summary agent**: [summary_agent.py](summary_agent.py)
  - Reads the current summary.
  - Rewrites or refines only the summary.
  - Saves changes through a write tool.

- **Experiences agent**: [experiences_agent.py](experiences_agent.py)
  - Handles work experience bullets and metadata.
  - Can add, edit, or remove bullets.
  - Can update title, company, location, and dates.
  - Can add or remove entire experience entries.

- **Educations agent**: [educations_agent.py](educations_agent.py)
  - Handles degree, institution, location, dates, GPA, and highlights.
  - Makes scoped education-only changes.

- **Skills agent**: [skills_agent.py](skills_agent.py)
  - Manages skill categories and individual skills.
  - Can add a skill, remove a skill, or move a skill between categories.

- **Projects agent**: [projects_agent.py](projects_agent.py)
  - Handles project descriptions, bullets, technologies, URLs, and project add/remove operations.

### Agent tools and state

- **Read tools**: [read_tools.py](read_tools.py)
  - Expose `get_resume()` and `get_section()`.
  - Let agents inspect current resume state before editing.

- **Write tools**: [write_tools.py](write_tools.py)
  - Contain the actual mutation functions.
  - Examples include `update_summary`, `add_skill`, `remove_skill`, `add_experience_bullet`, `update_education_fields`, and `add_project`.

- **Shared state**: [resume_state.py](resume_state.py) and [resume_data.json](resume_data.json)
  - Load a single in-memory resume object from JSON.
  - All prototype agents operate on this shared state.

### Important implementation note

The agent files show the intended **multi-agent architecture**, but the deployed product currently runs through [app/main.py](app/main.py) and does not invoke this hierarchy. Also, the agent files import `unibot_resume...` package paths that are not present in the current repo layout, so this layer should be treated as a prototype design unless it is restructured and integrated.

## Local development

Requirements: Python 3.12+ and optionally Ollama with `llama3:latest`.

```powershell
git clone https://github.com/Samik123Mit/unibot-resume-agent.git
cd unibot-resume-agent
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Open `http://127.0.0.1:8001`.

Run tests:

```powershell
pytest -q
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Production | SQLAlchemy URL; use PostgreSQL in deployment |
| `JWT_SECRET` | Production | Long random signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Session lifetime; default `10080` |
| `UPLOAD_DIR` | Production | Persistent mounted directory for PDF revisions |
| `LLM_API_BASE` | Cloud AI | OpenAI-compatible API base URL |
| `LLM_API_KEY` | Cloud AI | Provider secret; never expose to the browser |
| `LLM_MODEL` | Cloud AI | Hosted model identifier |
| `OLLAMA_MODEL` | Local only | Defaults to `llama3:latest` |

The server falls back to local Ollama when hosted-provider variables are absent. A cloud deployment must configure a hosted model because it cannot reach a developer machine’s Ollama service.

## Deployment

The repository includes:

- `Dockerfile` for deterministic container builds.
- `render.yaml` for a free demo web service and free Render PostgreSQL.
- `.github/workflows/ci.yml` for automated tests.
- `docker-compose.yml` for local PostgreSQL integration.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for rollout, secrets, smoke tests, backups, and rollback.

## API overview

| Area | Endpoints |
|---|---|
| Session | `/api/auth/guest`, `/api/auth/register`, `/api/auth/login`, `/api/me` |
| Resumes | `/api/resumes`, `/api/resumes/import`, `/api/resumes/{id}` |
| AI review | `/selection-edit`, `/apply-selection`, `/command` |
| ATS | `/ats` |
| PDF | `/preview`, `/pdf-layout`, `/pdf-page/{page}` |
| Recovery | `/undo`, `/reset`, `/revisions` |

Interactive OpenAPI documentation is available at `/docs` while the API runs.

## Test status

The suite covers tenant isolation, ATS output, proposal/approval behavior, vague-prompt clarification, exact PDF replacement, whole-CV PDF updates, and bold-style preservation. See [docs/TESTING.md](docs/TESTING.md) for the complete matrix.

## Safety and limitations

- Missing ATS keywords should be added only when they truthfully represent the candidate.
- The original PDF and extracted source text are retained for recovery.
- Scanned PDFs without a text layer require OCR before exact replacement.
- A substantially longer replacement can overflow the original text box; concise suggestions are preferred.
- Hosted production AI requires a server-side provider key.
- The free Render demo uses temporary PDF storage; uploaded files disappear on service restart/spin-down. Free Render PostgreSQL expires after 30 days.

## Documentation

- [Master technical document](docs/MASTER_DOCUMENT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Testing strategy and cases](docs/TESTING.md)
- [Deployment and operations](docs/DEPLOYMENT.md)

## License

No open-source license has been selected. All rights remain with the repository owner until a license is added.
