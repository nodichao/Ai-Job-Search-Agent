# AI Job Search Agent

An AI-powered job search agent designed to help users discover, analyze, filter, match, and prepare applications for relevant job opportunities.

The project focuses on source reliability, technical feasibility, explainability, modularity, and human control.

## 🎯 Project Goal

```text
User Profile
     ↓
Search
     ↓
Collect
     ↓
Normalize
     ↓
Deduplicate
     ↓
Filter
     ↓
Match
     ↓
Explain
     ↓
Recommend
     ↓
User decides
     ↓
POSTULER
     ↓
Application workflow
```

The agent assists the user; the final decision remains with the user.

## 🌍 Search Scope

The project prioritizes:

1. Dakar
2. Senegal
3. West Africa
4. Africa
5. International
6. Remote

## 🧩 Core Architecture

```text
External Sources
       ↓
   Connectors
       ↓
   Raw Data
       ↓
    Parsing
       ↓
 Transformation
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
      User
       ↓
   Application
```

Connectors isolate external-source integration from the core job-search logic. The rest of the system operates on a normalized `JobOffer` model.

## 🔎 Source Strategy

The first connector study focuses on:

- RemoteOK
- Himalayas
- We Work Remotely
- Greenhouse
- Lever
- Ashby
- Recruitee
- ReliefWeb

A source is not considered operational simply because it exposes an API or public data.

> **Technical accessibility does not automatically imply authorization.**

APIs, feeds, authentication, terms of service, storage, redistribution, rate limits, and application capabilities must be verified before a connector is considered operational.

## 🔌 Connector Architecture

```text
External Source
      ↓
Connector
      ↓
Raw Data
      ↓
Parsing
      ↓
Transformation
      ↓
Normalization
      ↓
Deduplication
      ↓
JobOffer
```

The architecture can support:

- JSON / REST APIs
- RSS
- XML feeds
- MCP
- authenticated or partner-specific mechanisms where authorized

Common technical concerns include authentication, pagination, rate limiting, retries, error handling, parsing, normalization, deduplication, provenance, observability, and testing.

## 🧠 Matching and Recommendation

```text
JobOffer
   ↓
Filtering
   ↓
Profile ↔ Offer Matching
   ↓
Explanation
   ↓
Recommendation
```

Matching and recommendations should remain explainable: the system should identify why an offer is relevant to the user's profile and preferences.

## 👤 Application Workflow

The application workflow starts only after an explicit user decision to apply:

```text
Offer
  ↓
POSTULER
  ↓
Identify application method
  ↓
Identify requirements
  ↓
Prepare using UserProfile
  ↓
Check missing elements
  ↓
Execute application
  ↓
Application recorded
```

### Application methods

```text
ApplicationMethod
├── API
└── EXTERNAL
    ├── SITE_REFERENCE
    ├── FORM
    └── EMAIL
```

### Execution modes

```text
ExecutionMode
├── API
├── MANUAL
└── AUTOMATED
```

Manual execution can still involve substantial agent preparation; the final submission remains under human control.

Email can be manual or automated through an authenticated and authorized email service.

Documents such as a CV, cover letter, diploma, or portfolio are modeled as **application requirements**, not application methods.

## 📚 Documentation

```text
docs/
├── architecture/
│   ├── project-context.md
│   ├── application-workflow.md
│   ├── connectors.md
│   └── connector-implementation-guide.md
│
├── research/
│   ├── research-protocol.md
│   └── sources-master.md
│
└── implementation/
    └── connector-implementation-plan.md
```

- **Architecture** — how the system is designed.
- **Research** — which sources are considered and how they are evaluated.
- **Implementation** — how the validated architecture will be translated into software.

Mermaid diagrams are embedded directly in Markdown so the documentation and its visual representations evolve together under Git version control.

## 🛡️ Design Principles

### 1. No assumption of authorization
Technical access is not treated as contractual permission.

### 2. Primary-source verification
Official documentation, terms, APIs, and other primary sources are preferred when validating source capabilities.

### 3. No bypassing restrictions
The system must not bypass authentication, CAPTCHA, anti-bot protections, rate limits, or other technical restrictions.

### 4. Human-in-the-loop
The user remains in control of important decisions, especially the decision to apply and manual application submissions.

### 5. Modularity
Each external source is isolated behind a connector.

### 6. Normalization
Different source formats converge toward a common internal `JobOffer` model.

### 7. Explainability
Matching and recommendations should provide understandable reasons rather than unexplained scores.

### 8. Security
Secrets such as API keys, tokens, passwords, OAuth credentials, and cookies must never be committed to the repository.

### 9. Incremental implementation
Architecture is documented before technology-specific implementation choices are prematurely locked in.

## 🚧 Current Status

The project is currently in the **architecture and connector-study phase**.

The first eight sources have been studied, but none should be considered fully operational until its connector passes the project's validation criteria.

The application workflow has also been modeled conceptually, including application methods, execution modes, requirements, and human-in-the-loop behavior.

## 📁 Repository Structure

The repository is being built incrementally.

The initial repository contains documentation and project configuration. Implementation directories such as `src/`, `tests/`, and `scripts/` will be introduced as their architecture is concretely defined.

The future implementation is expected to separate:

```text
src/
├── domain/
├── connectors/
├── pipeline/
├── application/
└── infrastructure/
```

## 📖 Where to Start

1. [`project-context.md`](docs/architecture/project-context.md) — overall project scope and architecture
2. [`sources-master.md`](docs/research/sources-master.md) — source registry
3. [`research-protocol.md`](docs/research/research-protocol.md) — research and validation rules
4. [`connectors.md`](docs/architecture/connectors.md) — connector technical reference
5. [`connector-implementation-plan.md`](docs/implementation/connector-implementation-plan.md) — implementation plan
6. [`application-workflow.md`](docs/architecture/application-workflow.md) — workflow after `POSTULER`

## ⚠️ Important

A source being listed in the project does **not** mean that:

- its API is authorized for the intended use;
- its data may automatically be stored or redistributed;
- its application mechanism may automatically be automated;
- its connector is operational.

These capabilities must be independently verified before implementation or production use.
