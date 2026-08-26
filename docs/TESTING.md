# Testing Strategy and Test Cases

## Automated suite

Run `pytest -q`.

| ID | Area | Scenario | Expected result |
|---|---|---|---|
| AUTH-01 | Tenancy | User B lists resumes after User A creates one | Empty list; no cross-tenant data |
| ATS-01 | Scoring | Analyze a CV against a job description | Score is 0–100 with missing terms and disclosed components |
| AI-01 | Command review | Add PostgreSQL to skills | Proposal returned first; mutation requires confirmation |
| AI-02 | Clarification | Prompt is “Improve it” | Targeted clarification question; no mutation |
| PDF-01 | Line edit | Replace exact PDF text | Old text removed and replacement extractable |
| PDF-02 | Whole-CV edit | Modify technical skills line | One changed line written into new PDF |
| PDF-03 | Formatting | Replace bold heading | Replacement remains bold |

## Browser acceptance matrix

| ID | Flow | Pass condition |
|---|---|---|
| UI-01 | Import | Page images and selectable text overlay appear |
| UI-02 | Line selection | Line highlights; selection card contains exact text |
| UI-03 | Drag selection | Selection card contains only dragged substring |
| UI-04 | Vague request | Clarification appears; apply button remains hidden |
| UI-05 | Approval | PDF regenerates only after approval |
| UI-06 | Whole-CV approval | Correct PDF line updates |
| UI-07 | ATS staging | Term is staged as a command, not auto-inserted |
| UI-08 | Undo | Prior text/PDF returns |
| UI-09 | Reset | Original uploaded PDF/text returns |
| UI-10 | Download | Current approved PDF downloads |

## Manual production smoke test

1. Open `/api/health` and expect `{"status":"ok"}`.
2. Create a guest workspace.
3. Upload a text-layer PDF under 8 MB.
4. Verify line and drag selection.
5. Verify vague-prompt clarification.
6. Generate and approve a precise rewrite.
7. Confirm the preview changes and downloaded PDF contains the replacement.
8. Run ATS analysis and open both cited sources.
9. Stage one truthful missing term, approve it, then undo it.
10. Reset and confirm the source PDF returns.

## Future LLM evaluation suite

- Factual preservation rate.
- Unsupported-claim/hallucination rate.
- Section-routing accuracy.
- Clarification precision on ambiguous prompts.
- Human acceptance rate by edit category.
- PDF mapping success by document generator and font.
