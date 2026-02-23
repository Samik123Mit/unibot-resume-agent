"""
Read-only tools — let agents inspect the resume without modifying it.
"""

import json
from unibot_resume.resume_state import RESUME


def get_resume() -> dict:
    """
    Return the complete resume as a dict.
    Use this to get full context before making any edits.
    """
    return {"status": "success", "resume": RESUME}


def get_section(section_name: str) -> dict:
    """
    Return a single section of the resume.

    Args:
        section_name: One of 'personal', 'summary', 'experiences',
                      'educations', 'skills', 'projects'.
    """
    section_name = section_name.lower().strip()
    valid = {"personal", "summary", "experiences", "educations", "skills", "projects"}
    if section_name not in valid:
        return {
            "status": "error",
            "message": f"Unknown section '{section_name}'. Valid sections: {sorted(valid)}",
        }
    return {"status": "success", "section": section_name, "data": RESUME.get(section_name)}
