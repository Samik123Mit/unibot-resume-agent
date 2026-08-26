# System Architecture

## Deployment topology

```mermaid
flowchart LR
    Internet --> TLS[Render TLS edge]
    TLS --> Web[FastAPI Docker service]
    Web --> PG[(Managed PostgreSQL)]
    Web --> Disk[(Persistent disk /var/data)]
    Web --> LLM[OpenAI-compatible LLM API]
    GHA[GitHub Actions] -->|tested source| Web
```

## Trust boundaries

| Boundary | Controls |
|---|---|
| Browser → API | Bearer JWT, request validation, upload limits |
| API → database | Parameterized SQLAlchemy queries, ownership predicates |
| API → PDF storage | Internal paths only; authenticated download/render endpoints |
| API → LLM | Server-side secret, constrained prompt, proposal-before-apply |
| User → AI mutation | Clarification and explicit approval gate |

## Component responsibilities

- **Browser:** upload, exact page display, selectable overlay, review/approval, download.
- **FastAPI:** authentication, tenancy, orchestration, validation and OpenAPI.
- **SQLAlchemy/PostgreSQL:** users, resume state and revision records.
- **PDF engine:** text localization, style-aware replacement, rendering and revision output.
- **LLM adapter:** local Ollama development or hosted OpenAI-compatible inference.
- **ATS analyzer:** deterministic BM25/evidence/structure calculation.

## Data lifecycle

```mermaid
flowchart TD
    Upload --> Source[Immutable source PDF + source text]
    Source --> Proposal[AI or ATS proposal]
    Proposal -->|reject| Source
    Proposal -->|approve| Revision[New PDF + database revision]
    Revision --> Download
    Revision --> Undo
    Revision --> Reset[Restore source pointers/text]
```

See [MASTER_DOCUMENT.md](MASTER_DOCUMENT.md) for detailed flows and decisions.
