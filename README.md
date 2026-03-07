# Unibot Resume Agent

> AI-powered resume editing assistant built with Google Agent Development Kit (ADK).
> Natural language → structured resume edits via a multi-agent hierarchy.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How to Change the Resume JSON](#how-to-change-the-resume-json)
- [Agent Hierarchy](#agent-hierarchy)
- [Tool List & Purpose](#tool-list--purpose)
- [Sample Test Queries](#sample-test-queries)
- [Prompt Design](#prompt-design)
- [Project Structure](#project-structure)

---

## Quick Start

### Prerequisites

- Python 3.10+
- A Google Gemini API key — get one free at https://aistudio.google.com/app/apikey

### 1. Clone the repo

```bash
git clone https://github.com/Samik123Mit/unibot-resume-agent
cd unibot-resume-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows CMD
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

Edit the `.env` file in the project root:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### 5. Run the agent

**Web interface (recommended):**
```bash
adk web
```
Open [http://localhost:8000](http://localhost:8000) → select **unibot** from the agent dropdown → start chatting.

**CLI interface:**
```bash
adk run unibot_resume
```

---

## How to Change the Resume JSON

> **To use your own resume, edit `unibot_resume/resume_data.json` and restart the agent.**

The file is loaded once at startup into an in-memory dict. All agents read and write from that dict via tools.

### Resume JSON Schema

```json
{
  "personal": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "linkedin": "string",
    "website": "string"
  },
  "summary": "string — 3-5 sentence professional summary",
  "experiences": [
    {
      "id": "exp_1",
      "title": "string",
      "company": "string",
      "location": "string",
      "start_date": "string",
      "end_date": "string",
      "bullets": ["string"]
    }
  ],
  "educations": [
    {
      "id": "edu_1",
      "degree": "string",
      "institution": "string",
      "location": "string",
      "start_date": "string",
      "end_date": "string",
      "gpa": "string",
      "highlights": ["string"]
    }
  ],
  "skills": [
    {
      "id": "skill_1",
      "category": "string",
      "items": ["string"]
    }
  ],
  "projects": [
    {
      "id": "proj_1",
      "name": "string",
      "description": "string",
      "technologies": ["string"],
      "bullets": ["string"],
      "url": "string"
    }
  ]
}
```

**ID convention:** `exp_N`, `edu_N`, `skill_N`, `proj_N` — keep them unique within each section. The agents use these IDs to target specific entries.

---

## Agent Hierarchy

```
unibot  (root agent)
│
│  Handles: greetings, general career Q&A, routing resume edit requests
│
└── resume_agent  (Resume Sub-Agent)
    │
    │  Handles: section identification, routes to correct section agent
    │
    ├── summary_agent       — rewrites / refines the professional summary
    ├── experiences_agent   — add/edit/remove bullets, update job fields
    ├── educations_agent    — update degree, GPA, dates, highlights
    ├── skills_agent        — add/remove skills, manage categories
    └── projects_agent      — add/remove projects, edit descriptions/bullets
```

### How routing works

1. **Unibot** receives every message. It answers general career questions directly (interview prep, salary negotiation, job search, etc.). If the message involves any resume edit, it delegates to `resume_agent`.

2. **resume_agent** identifies which section is targeted from the user's phrasing and delegates to the correct section agent. It does not edit the resume itself.

3. **Section agents** call read tools first, apply the change via write tools, and confirm the result to the user. Each agent only has access to tools for its own section — it cannot accidentally touch other sections.

---

## Tool List & Purpose

All tools live in `unibot_resume/tools/`. They operate on a single global `RESUME` dict loaded from `resume_data.json` at startup.

### Read Tools (`tools/read_tools.py`)

| Tool | Purpose |
|------|---------|
| `get_resume()` | Returns the full resume dict |
| `get_section(section_name)` | Returns one section by name (`summary`, `experiences`, `educations`, `skills`, `projects`) |

### Write Tools (`tools/write_tools.py`)

#### Summary

| Tool | Purpose |
|------|---------|
| `update_summary(text)` | Replace the entire summary string |

#### Experiences

| Tool | Purpose |
|------|---------|
| `get_experience_ids()` | List all experiences with their IDs, titles, and companies |
| `add_experience_bullet(exp_id, bullet)` | Append a new bullet to an experience |
| `update_experience_bullet(exp_id, index, bullet)` | Replace bullet at 0-based index |
| `remove_experience_bullet(exp_id, index)` | Remove bullet at 0-based index |
| `update_experience_fields(exp_id, ...)` | Update title / company / location / dates |
| `add_experience(title, company, ...)` | Add a brand-new experience entry |
| `remove_experience(exp_id)` | Delete an experience entirely |

#### Educations

| Tool | Purpose |
|------|---------|
| `get_education_ids()` | List all education entries with IDs |
| `update_education_fields(edu_id, ...)` | Update degree / school / GPA / dates |
| `add_education_highlight(edu_id, text)` | Add an honor or academic highlight |
| `remove_education_highlight(edu_id, index)` | Remove highlight at 0-based index |

#### Skills

| Tool | Purpose |
|------|---------|
| `get_skills()` | Return all skills grouped by category |
| `add_skill(skill, category)` | Add a skill; creates category if it doesn't exist |
| `remove_skill(skill)` | Remove skill by name (case-insensitive) |
| `move_skill_to_category(skill, category)` | Move a skill to a different category |

#### Projects

| Tool | Purpose |
|------|---------|
| `get_project_ids()` | List all projects with IDs and names |
| `update_project_description(proj_id, text)` | Rewrite the short project description |
| `add_project_bullet(proj_id, bullet)` | Append a bullet/achievement to a project |
| `update_project_bullet(proj_id, index, bullet)` | Replace bullet at 0-based index |
| `add_project(name, description, technologies, ...)` | Add a new project entry |
| `remove_project(proj_id)` | Delete a project entirely |
| `update_project_fields(proj_id, ...)` | Update project name / technologies / URL |

Every write tool validates inputs before touching the resume dict and returns `{"status": "success" | "error", "message": "..."}`. Invalid inputs (empty strings, bad IDs, out-of-range indices) return an error without corrupting the schema.

---

## Sample Test Queries

### Summary
```
Make my summary more senior
Rewrite my summary for leadership roles
Shorten my summary to 2 sentences
Tailor my summary for a machine learning engineer role
```

### Experiences
```
Add a leadership bullet to my first experience
Improve my first job bullets for impact
Add a bullet about cross-team collaboration to my second job
Update my title at TechCorp to Staff Engineer
Add a new experience at Google as a Software Engineer starting Jan 2024
```

### Skills
```
Add Python to my skills
Add PyTorch to a new Machine Learning category
Remove MongoDB from my skills
Add Rust to Languages
```

### Projects
```
Remove my second project
Add a project about an AI chatbot built with LangChain and FastAPI
Improve the description of my first project
Add a bullet about user growth to DevDash
```

### Education
```
Update my GPA to 3.9
Add Phi Beta Kappa as an honor to my education
Update my graduation year to 2020
```

### General career Q&A (handled by Unibot directly, no delegation)
```
How do I prepare for a system design interview?
What is a good summary length for an entry-level resume?
How do I negotiate a higher salary?
What should I put on my resume if I have no work experience?
```

---

## Prompt Design

### Core philosophy: tight scope + forced tool usage

**1. Minimal tool authority per agent**
Each section agent is given only the tools for its own section. The summary agent cannot call `add_skill()`; the skills agent cannot touch bullets. This makes over-editing structurally impossible, not just instructed against.

**2. Tool-forcing language**
Every section agent's system prompt explicitly states:
- `"ALWAYS call get_section(...) first to read current content before editing"`
- `"ALWAYS call [write tool] to save edits — never just describe what you'd write"`

This eliminates the common LLM failure mode of narrating a change without actually executing it.

**3. Ordinal resolution before writing**
Experience and project agents are instructed to always call `get_experience_ids()` / `get_project_ids()` first, then map "first job" → `exp_1`, "second project" → `proj_2`. This prevents off-by-one errors when the user references entries positionally.

**4. Routing tables in prompts**
Both `unibot` and `resume_agent` include explicit keyword → agent routing tables (e.g. "summary / bio / intro → summary_agent"). This makes common-case routing deterministic while the LLM still handles edge cases gracefully.

**5. Minimal edit principle**
Section agent prompts explicitly say: *"Only edit what the user requests. Do not alter unrelated bullets, fields, or sections."* This prevents agents from helpfully over-rewriting content the user didn't ask to change.

**6. Confirmation after every write**
Every agent is instructed to show the updated content to the user after saving. This creates a visible feedback loop so the user can immediately catch and correct anything unexpected.

---

## Project Structure

```
unibot_resume/
├── agent.py                  # root_agent (Unibot) — ADK entry point
├── resume_state.py           # loads resume_data.json → global RESUME dict
├── resume_data.json          # ← EDIT THIS to change the resume
├── requirements.txt
├── .env                      # GOOGLE_API_KEY goes here (not committed)
├── tools/
│   ├── __init__.py
│   ├── read_tools.py         # get_resume, get_section
│   └── write_tools.py        # all mutation tools
└── sub_agents/
    ├── __init__.py
    ├── resume_agent.py       # section router
    ├── summary_agent.py
    ├── experiences_agent.py
    ├── educations_agent.py
    ├── skills_agent.py
    └── projects_agent.py
```

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Agent framework | Google ADK (`google-adk`) |
| LLM | Gemini 2.0 Flash |
| Resume store | In-memory dict loaded from JSON |
| Language | Python 3.10+ |
