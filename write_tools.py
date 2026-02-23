"""
Write tools — all resume mutations happen through these functions.
Each function validates inputs before touching RESUME so the schema stays intact.
"""

import copy
import json
from typing import Optional
from unibot_resume.resume_state import RESUME


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────────

def update_summary(text: str) -> dict:
    """
    Replace the resume summary with new text.

    Args:
        text: The new summary string. Must be non-empty.
    """
    if not text or not text.strip():
        return {"status": "error", "message": "Summary text cannot be empty."}
    RESUME["summary"] = text.strip()
    return {"status": "success", "message": "Summary updated.", "summary": RESUME["summary"]}


# ──────────────────────────────────────────────────────────────────────────────
# EXPERIENCES
# ──────────────────────────────────────────────────────────────────────────────

def _find_experience(exp_id: str) -> Optional[dict]:
    for exp in RESUME.get("experiences", []):
        if exp["id"] == exp_id:
            return exp
    return None


def get_experience_ids() -> dict:
    """Return all experience IDs and titles so agents can reference the right entry."""
    return {
        "status": "success",
        "experiences": [
            {"id": e["id"], "title": e["title"], "company": e["company"]}
            for e in RESUME.get("experiences", [])
        ],
    }


def add_experience_bullet(exp_id: str, bullet: str) -> dict:
    """
    Append a new bullet point to a specific experience entry.

    Args:
        exp_id: The id of the experience (e.g. 'exp_1').
        bullet: The bullet text to add. Should be action-oriented and quantified.
    """
    exp = _find_experience(exp_id)
    if not exp:
        return {"status": "error", "message": f"Experience '{exp_id}' not found."}
    if not bullet.strip():
        return {"status": "error", "message": "Bullet text cannot be empty."}
    exp["bullets"].append(bullet.strip())
    return {"status": "success", "message": f"Bullet added to '{exp_id}'.", "bullets": exp["bullets"]}


def update_experience_bullet(exp_id: str, bullet_index: int, bullet: str) -> dict:
    """
    Replace a specific bullet in an experience entry.

    Args:
        exp_id: The id of the experience.
        bullet_index: 0-based index of the bullet to replace.
        bullet: The new bullet text.
    """
    exp = _find_experience(exp_id)
    if not exp:
        return {"status": "error", "message": f"Experience '{exp_id}' not found."}
    bullets = exp.get("bullets", [])
    if bullet_index < 0 or bullet_index >= len(bullets):
        return {"status": "error", "message": f"bullet_index {bullet_index} out of range (0–{len(bullets)-1})."}
    bullets[bullet_index] = bullet.strip()
    return {"status": "success", "message": "Bullet updated.", "bullets": bullets}


def remove_experience_bullet(exp_id: str, bullet_index: int) -> dict:
    """
    Remove a bullet from an experience entry.

    Args:
        exp_id: The id of the experience.
        bullet_index: 0-based index of the bullet to remove.
    """
    exp = _find_experience(exp_id)
    if not exp:
        return {"status": "error", "message": f"Experience '{exp_id}' not found."}
    bullets = exp.get("bullets", [])
    if bullet_index < 0 or bullet_index >= len(bullets):
        return {"status": "error", "message": f"bullet_index {bullet_index} out of range."}
    removed = bullets.pop(bullet_index)
    return {"status": "success", "message": f"Removed bullet: '{removed}'.", "bullets": bullets}


def update_experience_fields(exp_id: str, title: Optional[str] = None,
                              company: Optional[str] = None,
                              location: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> dict:
    """
    Update metadata fields (title, company, location, dates) for an experience.
    Only pass the fields you want to change; omit the rest.

    Args:
        exp_id: The id of the experience to update.
        title: New job title (optional).
        company: New company name (optional).
        location: New location (optional).
        start_date: New start date string (optional).
        end_date: New end date string (optional).
    """
    exp = _find_experience(exp_id)
    if not exp:
        return {"status": "error", "message": f"Experience '{exp_id}' not found."}
    if title:
        exp["title"] = title.strip()
    if company:
        exp["company"] = company.strip()
    if location:
        exp["location"] = location.strip()
    if start_date:
        exp["start_date"] = start_date.strip()
    if end_date:
        exp["end_date"] = end_date.strip()
    return {"status": "success", "message": f"Experience '{exp_id}' fields updated.", "experience": exp}


def add_experience(title: str, company: str, location: str,
                   start_date: str, end_date: str, bullets: list) -> dict:
    """
    Add a completely new experience entry.

    Args:
        title: Job title.
        company: Company name.
        location: Work location.
        start_date: Start date string (e.g. 'Jan 2020').
        end_date: End date string (e.g. 'Dec 2022' or 'Present').
        bullets: List of bullet strings.
    """
    existing_ids = [e["id"] for e in RESUME.get("experiences", [])]
    new_id = f"exp_{len(existing_ids) + 1}"
    while new_id in existing_ids:
        new_id = f"exp_{int(new_id.split('_')[1]) + 1}"
    new_exp = {
        "id": new_id,
        "title": title.strip(),
        "company": company.strip(),
        "location": location.strip(),
        "start_date": start_date.strip(),
        "end_date": end_date.strip(),
        "bullets": [b.strip() for b in bullets if b.strip()],
    }
    RESUME["experiences"].insert(0, new_exp)
    return {"status": "success", "message": f"Added experience '{new_id}'.", "experience": new_exp}


def remove_experience(exp_id: str) -> dict:
    """
    Remove an experience entry entirely.

    Args:
        exp_id: The id of the experience to remove.
    """
    experiences = RESUME.get("experiences", [])
    for i, exp in enumerate(experiences):
        if exp["id"] == exp_id:
            removed = experiences.pop(i)
            return {"status": "success", "message": f"Removed experience '{exp_id}' ({removed['title']} at {removed['company']})."}
    return {"status": "error", "message": f"Experience '{exp_id}' not found."}


# ──────────────────────────────────────────────────────────────────────────────
# EDUCATIONS
# ──────────────────────────────────────────────────────────────────────────────

def _find_education(edu_id: str) -> Optional[dict]:
    for edu in RESUME.get("educations", []):
        if edu["id"] == edu_id:
            return edu
    return None


def get_education_ids() -> dict:
    """Return all education IDs and degrees."""
    return {
        "status": "success",
        "educations": [
            {"id": e["id"], "degree": e["degree"], "institution": e["institution"]}
            for e in RESUME.get("educations", [])
        ],
    }


def update_education_fields(edu_id: str, degree: Optional[str] = None,
                             institution: Optional[str] = None,
                             location: Optional[str] = None,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             gpa: Optional[str] = None) -> dict:
    """
    Update metadata fields for an education entry.

    Args:
        edu_id: The id of the education entry.
        degree: New degree string (optional).
        institution: New institution name (optional).
        location: New location (optional).
        start_date: New start date (optional).
        end_date: New end date (optional).
        gpa: New GPA string (optional).
    """
    edu = _find_education(edu_id)
    if not edu:
        return {"status": "error", "message": f"Education '{edu_id}' not found."}
    if degree:
        edu["degree"] = degree.strip()
    if institution:
        edu["institution"] = institution.strip()
    if location:
        edu["location"] = location.strip()
    if start_date:
        edu["start_date"] = start_date.strip()
    if end_date:
        edu["end_date"] = end_date.strip()
    if gpa is not None:
        edu["gpa"] = gpa.strip()
    return {"status": "success", "message": f"Education '{edu_id}' updated.", "education": edu}


def add_education_highlight(edu_id: str, highlight: str) -> dict:
    """
    Add a highlight/achievement to an education entry.

    Args:
        edu_id: The id of the education entry.
        highlight: The highlight text to add.
    """
    edu = _find_education(edu_id)
    if not edu:
        return {"status": "error", "message": f"Education '{edu_id}' not found."}
    edu.setdefault("highlights", []).append(highlight.strip())
    return {"status": "success", "message": "Highlight added.", "highlights": edu["highlights"]}


def remove_education_highlight(edu_id: str, highlight_index: int) -> dict:
    """
    Remove a highlight from an education entry.

    Args:
        edu_id: The id of the education entry.
        highlight_index: 0-based index of the highlight to remove.
    """
    edu = _find_education(edu_id)
    if not edu:
        return {"status": "error", "message": f"Education '{edu_id}' not found."}
    highlights = edu.get("highlights", [])
    if highlight_index < 0 or highlight_index >= len(highlights):
        return {"status": "error", "message": f"highlight_index {highlight_index} out of range."}
    removed = highlights.pop(highlight_index)
    return {"status": "success", "message": f"Removed highlight: '{removed}'."}


# ──────────────────────────────────────────────────────────────────────────────
# SKILLS
# ──────────────────────────────────────────────────────────────────────────────

def _find_skill_category(skill_id: str) -> Optional[dict]:
    for s in RESUME.get("skills", []):
        if s["id"] == skill_id:
            return s
    return None


def _find_skill_category_by_name(category: str) -> Optional[dict]:
    for s in RESUME.get("skills", []):
        if s["category"].lower() == category.lower():
            return s
    return None


def get_skills() -> dict:
    """Return all skills grouped by category."""
    return {"status": "success", "skills": RESUME.get("skills", [])}


def add_skill(skill: str, category: Optional[str] = None) -> dict:
    """
    Add a skill to a category. If the category doesn't exist, it will be created.
    If category is omitted, best-guess the correct existing category.

    Args:
        skill: The skill name to add (e.g. 'Python', 'TensorFlow').
        category: The category name (e.g. 'Languages', 'Frameworks & Tools'). Optional.
    """
    skill = skill.strip()
    if not skill:
        return {"status": "error", "message": "Skill name cannot be empty."}

    # Check if skill already exists
    for cat in RESUME.get("skills", []):
        if skill.lower() in [s.lower() for s in cat["items"]]:
            return {"status": "error", "message": f"'{skill}' already exists in category '{cat['category']}'."}

    if category:
        cat = _find_skill_category_by_name(category)
        if cat:
            cat["items"].append(skill)
            return {"status": "success", "message": f"Added '{skill}' to '{cat['category']}'.", "category": cat}
        else:
            # Create new category
            new_id = f"skill_{len(RESUME.get('skills', [])) + 1}"
            new_cat = {"id": new_id, "category": category.strip(), "items": [skill]}
            RESUME.setdefault("skills", []).append(new_cat)
            return {"status": "success", "message": f"Created new category '{category}' with '{skill}'.", "category": new_cat}
    else:
        # Default: add to first category
        if RESUME.get("skills"):
            RESUME["skills"][0]["items"].append(skill)
            return {"status": "success", "message": f"Added '{skill}' to '{RESUME['skills'][0]['category']}'.",
                    "category": RESUME["skills"][0]}
        else:
            new_cat = {"id": "skill_1", "category": "Skills", "items": [skill]}
            RESUME["skills"] = [new_cat]
            return {"status": "success", "message": f"Added '{skill}' to new category 'Skills'."}


def remove_skill(skill: str) -> dict:
    """
    Remove a skill by name from whichever category it is in.

    Args:
        skill: The exact or case-insensitive name of the skill to remove.
    """
    skill = skill.strip()
    for cat in RESUME.get("skills", []):
        for existing in cat["items"]:
            if existing.lower() == skill.lower():
                cat["items"].remove(existing)
                return {"status": "success", "message": f"Removed '{existing}' from '{cat['category']}'."}
    return {"status": "error", "message": f"Skill '{skill}' not found in any category."}


def move_skill_to_category(skill: str, new_category: str) -> dict:
    """
    Move a skill from its current category to another (creating category if needed).

    Args:
        skill: The skill name to move.
        new_category: The target category name.
    """
    # First remove
    result = remove_skill(skill)
    if result["status"] == "error":
        return result
    # Then add to new category
    return add_skill(skill, new_category)


# ──────────────────────────────────────────────────────────────────────────────
# PROJECTS
# ──────────────────────────────────────────────────────────────────────────────

def _find_project(proj_id: str) -> Optional[dict]:
    for p in RESUME.get("projects", []):
        if p["id"] == proj_id:
            return p
    return None


def get_project_ids() -> dict:
    """Return all project IDs and names."""
    return {
        "status": "success",
        "projects": [
            {"id": p["id"], "name": p["name"]}
            for p in RESUME.get("projects", [])
        ],
    }


def update_project_description(proj_id: str, description: str) -> dict:
    """
    Update the short description of a project.

    Args:
        proj_id: The id of the project.
        description: The new description text.
    """
    proj = _find_project(proj_id)
    if not proj:
        return {"status": "error", "message": f"Project '{proj_id}' not found."}
    proj["description"] = description.strip()
    return {"status": "success", "message": f"Updated description for '{proj_id}'.", "project": proj}


def add_project_bullet(proj_id: str, bullet: str) -> dict:
    """
    Add a bullet/achievement to a project.

    Args:
        proj_id: The id of the project.
        bullet: The bullet text to add.
    """
    proj = _find_project(proj_id)
    if not proj:
        return {"status": "error", "message": f"Project '{proj_id}' not found."}
    proj.setdefault("bullets", []).append(bullet.strip())
    return {"status": "success", "message": "Bullet added.", "bullets": proj["bullets"]}


def update_project_bullet(proj_id: str, bullet_index: int, bullet: str) -> dict:
    """
    Replace a bullet in a project.

    Args:
        proj_id: The id of the project.
        bullet_index: 0-based index of bullet to replace.
        bullet: New bullet text.
    """
    proj = _find_project(proj_id)
    if not proj:
        return {"status": "error", "message": f"Project '{proj_id}' not found."}
    bullets = proj.get("bullets", [])
    if bullet_index < 0 or bullet_index >= len(bullets):
        return {"status": "error", "message": f"bullet_index {bullet_index} out of range."}
    bullets[bullet_index] = bullet.strip()
    return {"status": "success", "message": "Bullet updated.", "bullets": bullets}


def add_project(name: str, description: str, technologies: list,
                bullets: Optional[list] = None, url: Optional[str] = None) -> dict:
    """
    Add a new project entry.

    Args:
        name: Project name.
        description: Short description.
        technologies: List of technology strings.
        bullets: List of achievement bullets (optional).
        url: Project URL (optional).
    """
    existing_ids = [p["id"] for p in RESUME.get("projects", [])]
    new_id = f"proj_{len(existing_ids) + 1}"
    while new_id in existing_ids:
        new_id = f"proj_{int(new_id.split('_')[1]) + 1}"
    new_proj = {
        "id": new_id,
        "name": name.strip(),
        "description": description.strip(),
        "technologies": [t.strip() for t in technologies],
        "bullets": [b.strip() for b in (bullets or []) if b.strip()],
        "url": (url or "").strip(),
    }
    RESUME.setdefault("projects", []).append(new_proj)
    return {"status": "success", "message": f"Added project '{new_id}' — '{name}'.", "project": new_proj}


def remove_project(proj_id: str) -> dict:
    """
    Remove a project entry entirely.

    Args:
        proj_id: The id of the project to remove.
    """
    projects = RESUME.get("projects", [])
    for i, proj in enumerate(projects):
        if proj["id"] == proj_id:
            removed = projects.pop(i)
            return {"status": "success", "message": f"Removed project '{proj_id}' ('{removed['name']}')."}
    return {"status": "error", "message": f"Project '{proj_id}' not found."}


def update_project_fields(proj_id: str, name: Optional[str] = None,
                           technologies: Optional[list] = None,
                           url: Optional[str] = None) -> dict:
    """
    Update project metadata (name, technologies, url).

    Args:
        proj_id: The id of the project.
        name: New project name (optional).
        technologies: New technologies list (optional).
        url: New URL (optional).
    """
    proj = _find_project(proj_id)
    if not proj:
        return {"status": "error", "message": f"Project '{proj_id}' not found."}
    if name:
        proj["name"] = name.strip()
    if technologies is not None:
        proj["technologies"] = [t.strip() for t in technologies]
    if url is not None:
        proj["url"] = url.strip()
    return {"status": "success", "message": f"Project '{proj_id}' updated.", "project": proj}
