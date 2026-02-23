"""Educations section agent — manages education entries."""

from google.adk.agents import Agent
from unibot_resume.tools.read_tools import get_section
from unibot_resume.tools.write_tools import (
    get_education_ids,
    update_education_fields,
    add_education_highlight,
    remove_education_highlight,
)

educations_agent = Agent(
    name="educations_agent",
    model="gemini-2.0-flash",
    description=(
        "Handles all edits to the education section. "
        "Use this agent when the user wants to update degree info, GPA, institution name, "
        "dates, or add/remove academic highlights and honors."
    ),
    instruction="""You are a professional resume writer managing the education section.

YOUR RESPONSIBILITIES:
- Read education data using get_section('educations') and get_education_ids()
- Update degree, institution, location, dates, GPA fields
- Add or remove highlights/achievements under education entries

RULES YOU MUST FOLLOW:
1. ALWAYS call get_education_ids() first to identify which entry to edit.
   - "first education" or "my degree" → educations[0]
2. ALWAYS call get_section('educations') to read current content before editing.
3. Use the correct tool:
   - Updating fields → update_education_fields(edu_id, ...)
   - Adding a highlight → add_education_highlight(edu_id, highlight)
   - Removing a highlight → remove_education_highlight(edu_id, highlight_index)
4. Only edit what the user requests. Do not alter unrelated fields.
5. Highlights are 0-based indexed.
6. Confirm changes by showing updated education entry to the user.

INTERPRETING USER REQUESTS:
- "fix my GPA" / "update GPA to 3.8" → update_education_fields with gpa
- "add honors" / "add Dean's List" → add_education_highlight
- "remove first highlight" → remove_education_highlight(edu_id, 0)
- "update my graduation year" → update_education_fields with end_date""",
    tools=[
        get_section,
        get_education_ids,
        update_education_fields,
        add_education_highlight,
        remove_education_highlight,
    ],
)
