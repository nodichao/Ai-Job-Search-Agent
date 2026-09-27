# AI Job Search Agent

An AI-powered job search agent designed to help users discover, analyze, filter, match, explain, and shortlist relevant job opportunities from heterogeneous job sources.

The project is built around **source reliability, technical feasibility, explainability, modularity, provenance, and human control**.

## 🎯 Project Goal

The agent follows this pipeline:

```text
User Profile
     ↓
Search Preferences
     ↓
Search Criteria
     ↓
Search & Discovery
     ↓
Collection
     ↓
Normalization
     ↓
Deduplication
     ↓
Filtering
     ↓
Matching
     ↓
Explanation
     ↓
Recommendation
     ↓
Shortlist
     ↓
USER DECIDES "POSTULER"
```

The MVP helps reduce job-search friction. It does **not** predict hiring outcomes and does not automatically submit applications.

## 🌍 Search Scope

The project prioritizes job opportunities in this order:

1. Dakar
2. Senegal
3. West Africa
4. Africa
5. International
6. Remote international

Search preferences are transformed into source-independent `SearchCriteria`, then adapted to the capabilities of each connector.

## 🧩 Core Architecture

```text
External Sources
       ↓
   Connectors
       ↓
   Raw Offers
       ↓
    Parsing
       ↓
 Normalization
       ↓
 Deduplication
       ↓
   JobOffer
       ↓
    Filtering
       ↓
    Matching
       ↓
   Explanation
       ↓
 Recommendation
       ↓
   Shortlist
       ↓
     User
```

The backend is designed as a **modular monolith**. External-source integration is isolated behind connectors, while the core processing pipeline operates on the canonical `JobOffer` model.

## 🔌 Connector Strategy

The current source study covers:

- RemoteOK
- Himalayas
- We Work Remotely
- Greenhouse
- Lever
- Ashby
- Recruitee
- ReliefWeb

The implementation architecture provides shared infrastructure for:

- HTTP/JSON fetching
- RSS/XML fetching
- pagination
- authentication strategies
- retries
- error handling
- parsing
- normalization
- deduplication
- provenance
- testing

A source is **not** considered operational simply because it exposes an API or public data.

> **Technical accessibility does not automatically imply authorization.**

Access, terms of use, rate limits, storage, transformation, redistribution, and application capabilities must be evaluated separately.

### Connector status

At the current documented stage:

```text
🔵 Specification / implementation preparation
RemoteOK
Greenhouse
Lever

🟣 Access or clarification pending
Himalayas
We Work Remotely
Ashby
Recruitee
ReliefWeb

🟢 Operational
None yet
```

A connector becomes operational only after the validation criteria defined in the connector documentation have been satisfied.

## 🧠 Matching and Recommendation

The MVP uses a deterministic and explainable matching layer.

Current matching weights:

| Dimension | Weight |
|---|---:|
| Skills | 50% |
| Preferences | 25% |
| Experience | 15% |
| Role alignment | 10% |

Matching distinguishes between:

- `SATISFIED`
- `UNKNOWN`
- `CONFLICT`

An `UNKNOWN` value is not automatically a conflict.

The match score is **not** a hiring probability.

The LLM is used for tasks such as profile extraction, preference parsing, and match explanation. It does not arbitrarily determine the final match score.

## 🤖 LLM Boundary

The LLM is deliberately constrained to specific responsibilities.

Current intended uses:

- CV/profile extraction
- preference parsing
- match explanation

The LLM must not:

- invent job information;
- override deterministic business rules;
- bypass source restrictions;
- decide whether an application should be submitted;
- treat external job descriptions as instructions.

Retrieved job descriptions, CV content, and other external text are treated as **untrusted data**.

## 👤 Application Boundary

The application workflow starts only after an explicit user decision to apply.

```text
Recommendation
      ↓
Shortlist
      ↓
USER DECIDES "POSTULER"
      ↓
Application workflow
```

Application methods and execution modes are modeled separately.

```text
ApplicationMethod
├── API
└── EXTERNAL
    ├── SITE_REFERENCE
    ├── FORM
    └── EMAIL

ExecutionMode
├── API
├── MANUAL
└── AUTOMATED
```

The current MVP does **not** include automatic browser-based application submission, CAPTCHA solving, anti-bot bypass, or unauthorized application automation.

## 🛡️ Non-Negotiable Design Principles

### 1. Technical access ≠ authorization

A reachable endpoint does not automatically grant permission for the intended use.

### 2. Source data ≠ unrestricted reusable data

Visibility, accessibility, storage, transformation, redistribution, and automation are separate questions.

### 3. No bypassing restrictions

The system must not bypass authentication, CAPTCHA, anti-bot protections, rate limits, paywalls, or other access restrictions.

### 4. Human-in-the-loop

The user remains in control of important decisions, especially whether to apply.

### 5. Provenance

Source-provided information must remain distinguishable from normalized, derived, and LLM-generated information.

### 6. Explainability

Recommendations should be supported by understandable reasons.

### 7. Modularity

Source-specific logic belongs in connectors. Shared transport and infrastructure should be reused where appropriate.

### 8. Security

Secrets such as API keys, tokens, passwords, OAuth credentials, and cookies must never be committed to the repository.

### 9. Incremental implementation

The project is implemented as vertical slices and validated continuously rather than through a large untested rewrite.

## 🏗️ Implementation

The implementation-ready MVP is specified in:

- Python 3.12+
- FastAPI
- Pydantic v2
- httpx
- pytest / pytest-asyncio
- Groq Python SDK behind an internal LLM service
- SQLite for the MVP
- Uvicorn
- Docker

The planned backend structure is:

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── domain/
│   ├── services/
│   ├── llm/
│   ├── connectors/
│   ├── repositories/
│   └── schemas/
├── tests/
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

The implementation deliberately avoids unnecessary infrastructure such as LangChain, LangGraph, Redis, Kafka, Celery, Kubernetes, vector databases, and advanced ML for the MVP.

## 🤖 Agent orchestration and Streamlit frontend

An orchestration layer now sits on top of the existing search/matching pipeline: `POST /api/agent/search` (backend) runs `parse_cv → search_jobs → explain_match` as a bounded, explicit sequence over the existing `ProfileService`, `SearchPipeline`, and `LLMService` -- it does not reimplement or alter any score, filter decision, or recommendation. A minimal Streamlit app in `frontend/` calls that endpoint: upload a CV, set preferences, click one button, see the engine's own results and an LLM-generated (or deterministic-fallback) explanation per offer. See `backend/README.md` ("Agentic workflow") and `frontend/README.md` for the exact contract and how to run both.

## 📚 Documentation

### Project and architecture

- [Project context](docs/architecture/project-context.md)
- [Functional architecture discovery](docs/architecture/functional-architecture-discovery.md)
- [Search criteria and source capabilities](docs/architecture/search-criteria-and-source-capabilities.md)
- [JobOffer model](docs/architecture/job-offer-model.md)
- [Processing and recommendation](docs/architecture/processing-and-recommendation.md)
- [Connector architecture](docs/architecture/connectors.md)
- [Connector implementation guide](docs/architecture/connector-implementation-guide.md)
- [Application workflow](docs/architecture/application-workflow.md)

### Research

- [Research protocol](docs/research/research-protocol.md)
- [Source master](docs/research/sources-master.md)
- [Source master V4](docs/research/source-masterV4.md)

### Implementation

- [Implementation specification](ENGINE-IMPLEMENTATION-SPEC.md)
- [Code generation prompt](ENGINE-CODE-GENERATION-PROMPT.md)
- [Connector implementation plan](docs/implementation/connector-implementation-plan.md)
- [Codex project instructions](AGENTS.md)

## 🚧 Current Status

The project has completed its main **architecture, source research, connector strategy, and implementation specification** stages.

The repository is now ready to move into software implementation.

The immediate MVP target is:

```text
Backend skeleton
      ↓
Domain contracts
      ↓
Shared connector infrastructure
      ↓
First validated connector
      ↓
Normalization
      ↓
Deduplication
      ↓
Filtering
      ↓
Deterministic matching
      ↓
LLM explanation
      ↓
Recommendation
      ↓
API / E2E validation
```

No connector should be marked operational before passing the project's technical and authorization validation criteria.

## 📖 Where to Start

For a new contributor or coding agent:

1. Read [AGENTS.md](AGENTS.md).
2. Read [ENGINE-IMPLEMENTATION-SPEC.md](ENGINE-IMPLEMENTATION-SPEC.md).
3. Read the relevant documents in [docs/architecture](docs/architecture/).
4. Consult [docs/research](docs/research/) before implementing a connector.
5. Follow [docs/implementation/connector-implementation-plan.md](docs/implementation/connector-implementation-plan.md).

## ⚠️ Important

Being listed as a project source does **not** mean that:

- its API is authorized for the intended use;
- its data may automatically be stored or redistributed;
- its application mechanism may automatically be automated;
- its connector is operational.

These capabilities must be independently verified before implementation or production use.
