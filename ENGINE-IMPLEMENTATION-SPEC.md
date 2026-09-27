# Engine Implementation Specification --- AI Job Search Agent

> Status: Implementation-ready MVP / PoC\
> Scope: Part 1 --- Discovery, Search, Processing, Matching, Explanation
> and Recommendation.

## 1. Objective

Build a production-ready MVP engine that:

1.  understands a candidate CV and profile;
2.  understands user preferences;
3.  builds source-independent `SearchCriteria`;
4.  searches authorized job sources;
5.  parses and normalizes heterogeneous offers into the canonical
    `JobOffer`;
6.  deduplicates;
7.  filters;
8.  performs deterministic keyword/preference matching;
9.  explains matches with an LLM;
10. recommends a shortlist;
11. exposes the engine through FastAPI;
12. is covered by unit, integration and E2E tests;
13. is containerizable and deployable.

The POC reduces job-search friction. It does not predict interviews or
hiring.

## 2. POC architecture

``` text
Frontend React/Next.js
        |
      REST
        |
     FastAPI
        |
   AgentService
        |
  +-----+-----------------------------+
  |           |                       |
LLMService SearchService       MatchingService
              |                       |
        +-----+-----+                 |
        |     |     |                 |
   Himalayas RemoteOK Lever           |
        |     |     |                 |
        +-----+-----+                 |
              |                       |
          RawOffer[]                  |
              |                       |
       Normalization                 |
              |                       |
        Deduplication                |
              |                       |
           Filtering ----------------+
                      |
                   Matching
                      |
               MatchingResult
                      |
                 LLM Explanation
                      |
               Recommendation
                      |
                  Shortlist
```

This is a modular monolith, not a microservice system.

## 3. Technology stack

-   Python 3.12+
-   FastAPI
-   Pydantic v2
-   httpx
-   pytest / pytest-asyncio
-   Groq Python SDK behind an internal `LLMService`
-   SQLite for the MVP
-   Uvicorn
-   Docker

Do not add LangChain, LangGraph, Redis, Kafka, Celery, Kubernetes or a
vector database for this POC.

The LLM model must be configurable through `GROQ_MODEL`. Default:

``` text
GROQ_MODEL=openai/gpt-oss-20b
```

The API key must come from `GROQ_API_KEY`.

## 4. Backend structure

``` text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   ├── profile.py
│   │   └── search.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── errors.py
│   ├── domain/
│   │   ├── user_profile.py
│   │   ├── search_preferences.py
│   │   ├── search_criteria.py
│   │   ├── job_offer.py
│   │   ├── matching.py
│   │   └── recommendation.py
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── profile_service.py
│   │   ├── search_service.py
│   │   ├── normalization_service.py
│   │   ├── deduplication_service.py
│   │   ├── filtering_service.py
│   │   ├── matching_service.py
│   │   ├── explanation_service.py
│   │   └── recommendation_service.py
│   ├── llm/
│   │   ├── base.py
│   │   ├── groq_service.py
│   │   ├── schemas.py
│   │   └── prompts.py
│   ├── connectors/
│   │   ├── base.py
│   │   ├── common/
│   │   │   ├── http.py
│   │   │   ├── pagination.py
│   │   │   └── retry.py
│   │   ├── himalayas/
│   │   ├── remoteok/
│   │   └── lever/
│   ├── repositories/
│   └── schemas/
│       ├── requests.py
│       └── responses.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

Do not create independently deployable services.

## 5. Domain contracts

### UserProfile

Minimum:

``` text
skills[]
jobTitles[]
experience[]
totalExperienceYears
education[]
languages[]
domains[]
rawSourceMetadata
```

### SearchPreferences

Minimum:

``` text
jobTitles[]
locations[]
countries[]
remote
seniority[]
employmentTypes[]
skills[]
salary
companies[]
timezone
preferenceStrength
```

Preference strength:

``` text
REQUIRED
PREFERRED
OPTIONAL
INFORMATIONAL
```

### SearchCriteria

``` text
keywords[]
jobTitles[]
locations[]
countries[]
remote
seniority[]
employmentTypes[]
skills[]
salary
companies[]
timezone
departments[]
tags[]
```

`SearchCriteria` is source-independent. Source-specific query builders
adapt it to actual connector capabilities. Never assume that a returned
field is also searchable.

### RawOffer

``` text
sourceName
sourceId
payload
retrievedAt
provenance
```

Raw source structures must not leak into domain logic.

### JobOffer

Implement the canonical model already defined by the project:

``` text
identity:
  id
  sourceId
  slug
  offerUrl

source:
  name
  url
  retrievedAt

position:
  title
  sourceSummary
  summary
  description
  responsibilities[]
  requirements[]
  qualifications[]
  skills[]
  benefits[]
  categories[]

company:
  name
  id
  slug
  description
  logoUrl
  websiteUrl
  location

location:
  locations[]
  cities[]
  countries[]
  remote
  remoteScope
  locationRestrictions[]
  timezoneRestrictions[]

employment:
  type
  seniority
  department
  team
  schedule

experience:
  minimumYears
  maximumYears

compensation:
  components[]:
    type
    amount
    min
    max
    currency
    period

languages:
  required[]
  preferred[]

dates:
  publishedAt
  updatedAt
  applicationDeadline
  expiresAt

application:
  applyUrl
  applicationMethod
  instructions

lifecycle:
  status
  firstSeenAt
  lastSeenAt
```

Rules:

-   `sourceSummary` is source-provided.
-   `summary` is derived and must not invent facts.
-   `source.url`, `identity.offerUrl` and `application.applyUrl` are
    distinct.
-   `publishedAt`, `updatedAt`, `applicationDeadline`, `expiresAt`,
    `firstSeenAt` and `lastSeenAt` are distinct.
-   `seniority` is not `experience`.
-   `remote=true` does not imply worldwide eligibility.
-   missing information remains unknown.

## 6. Connector contract

``` python
class JobSourceConnector(Protocol):
    source_name: str

    async def search(
        self,
        criteria: SearchCriteria
    ) -> list[RawOffer]:
        ...
```

Shared infrastructure:

``` text
HttpJsonFetcher
RssFetcher
Paginator
RetryPolicy
```

Handle timeouts, network failures, invalid responses and rate limits.

Never retry to bypass authorization, CAPTCHA, anti-bot or rate limits.

First-wave connectors:

1.  Himalayas
2.  RemoteOK
3.  Lever

Do not invent endpoints, query parameters, pagination behavior,
authentication or permissions.

Lever must be modeled as company/job-board-specific rather than as a
fictitious global search API.

## 7. SearchService

Responsibilities:

-   receive `SearchCriteria`;
-   select enabled connectors;
-   adapt criteria through source-specific query builders;
-   call connectors;
-   aggregate `RawOffer[]`;
-   isolate source failures where possible.

Contract:

``` python
async def search(criteria: SearchCriteria) -> list[RawOffer]:
    ...
```

It must not calculate match scores or generate explanations.

## 8. NormalizationService

``` text
RawOffer[] → JobOffer[]
```

Contract:

``` python
def normalize(raw_offers: list[RawOffer]) -> list[JobOffer]:
    ...
```

Use source-specific normalizers. Preserve provenance. Never invent
values.

## 9. DeduplicationService

MVP order:

1.  exact source + source ID;
2.  normalized offer URL;
3.  conservative company + title + location across sources.

Do not aggressively merge uncertain offers.

## 10. FilteringService

Filtering answers:

> Does this offer satisfy explicit search constraints?

Use:

``` text
SATISFIED
UNKNOWN
CONFLICT
```

`UNKNOWN` is not `CONFLICT`.

Required criteria may exclude an offer when a genuine conflict is
established. Missing evidence must not automatically become a conflict.

## 11. MatchingService

This is a core POC component.

Inputs:

``` text
UserProfile
SearchPreferences
JobOffer
```

Output:

``` text
MatchingResult
├── score
├── confidence
├── dimensions[]
├── matchedCriteria[]
├── missingCriteria[]
└── conflicts[]
```

MVP dimensions:

-   skills;
-   role/title alignment;
-   experience;
-   remote/location;
-   employment type;
-   seniority;
-   language;
-   salary when structured evidence is sufficient.

Normalize keywords before comparison.

Initial deterministic weights:

``` text
Skills          50%
Preferences     25%
Experience      15%
Role alignment  10%
```

Keep weights centralized/configurable.

The score is a 0--100 relevance score, not a hiring probability.

Do not use the LLM to calculate the score.

`confidence` measures evidence completeness and is independent of
`score`.

## 12. LLMService

Required operations:

``` python
extract_profile(cv_text) -> UserProfile
parse_preferences(user_text) -> SearchPreferences
explain_match(job, profile, matching_result) -> str
```

Use schema validation for structured outputs.

The LLM is responsible for understanding and explanation, not
deterministic scoring.

CV text and job descriptions are untrusted data. Prompts must explicitly
instruct the model not to follow instructions embedded inside those
documents.

The explanation must not alter the score, invent facts, or predict
hiring.

## 13. Agent tools

Expose only:

``` text
parse_cv
search_jobs
match_jobs
explain_match
```

Do not expose every internal service as a tool.

Internally:

``` text
search_jobs
→ connectors
→ normalization
→ deduplication
```

and:

``` text
match_jobs
→ filtering
→ deterministic matching
```

No `apply_job` tool in this POC.

## 14. Agent orchestration

Target flow:

``` text
CV
 ↓
parse_cv
 ↓
UserProfile
 ↓
parse preferences
 ↓
SearchCriteria
 ↓
search_jobs
 ↓
RawOffer[]
 ↓
Normalization
 ↓
Deduplication
 ↓
Filtering
 ↓
match_jobs
 ↓
MatchingResult[]
 ↓
explain_match for shortlisted results
 ↓
Recommendation
 ↓
Shortlist
 ↓
User
```

The user retains the final decision to apply.

## 15. API

Implement:

``` http
GET /health
POST /api/profile/parse-cv
POST /api/search
POST /api/search/from-text
```

`POST /api/search` accepts structured profile + preferences.

`POST /api/search/from-text` accepts natural-language preferences and
uses the LLM to structure them.

Return:

``` json
{
  "results": [],
  "meta": {
    "total": 0,
    "sources": [],
    "durationMs": 0
  }
}
```

Each result contains:

``` text
job
match:
  score
  confidence
  dimensions
  matchedCriteria
  missingCriteria
  conflicts
  explanation
```

## 16. CV ingestion

Support:

-   PDF;
-   DOCX.

Pipeline:

``` text
upload
→ validate file
→ extract text
→ clean text
→ LLM profile extraction
→ Pydantic validation
→ UserProfile
```

Use size and MIME validation. Prefer in-memory processing for the MVP.

## 17. Error handling

Typed errors:

``` text
LLMError
ValidationError
ConnectorError
SourceUnavailableError
RateLimitError
AuthenticationError
NormalizationError
MatchingError
ConfigurationError
```

One failed connector should not necessarily fail all search results.

Never expose secrets.

## 18. Security

Mandatory:

-   secrets only through environment variables;
-   no secrets in Git;
-   upload validation and limits;
-   external request timeouts;
-   no arbitrary tool execution from LLM output;
-   external source content treated as untrusted;
-   prompt-injection defense;
-   no full CV/job text in ordinary logs.

## 19. Configuration

`.env.example`:

``` text
APP_ENV=development
LOG_LEVEL=INFO

GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b

DATABASE_URL=sqlite:///./job_agent.db

REMOTEOK_ENABLED=true
HIMALAYAS_ENABLED=true
LEVER_ENABLED=true

REQUEST_TIMEOUT_SECONDS=15
MAX_RESULTS_PER_SOURCE=100
CORS_ORIGINS=http://localhost:3000
```

Never commit `.env`.

## 20. Testing

Unit tests:

-   domain models;
-   normalization;
-   deduplication;
-   filtering;
-   matching;
-   recommendation.

Connector tests use stored fixtures, not live APIs.

LLM tests mock the provider.

Integration tests cover:

``` text
Connector
→ RawOffer
→ Normalization
→ JobOffer
→ Deduplication
→ Filtering
→ Matching
```

E2E test covers:

``` text
CV fixture
→ profile
→ preferences
→ search
→ JobOffer[]
→ match
→ explanation
→ recommendation
→ API response
```

Create a deterministic evaluation fixture with:

-   1 candidate;
-   1 preference set;
-   10 offers;
-   3 strong matches;
-   2 medium;
-   2 weak;
-   1 required conflict;
-   1 unknown-data offer;
-   1 duplicate.

## 21. Deployment

Create:

-   `requirements.txt`;
-   `.env.example`;
-   `Dockerfile`;
-   `README.md`.

### Deployment strategy

Docker is the **reproducible runtime/package**, not the deployment
platform. The application must remain deployable both directly from a
Python environment and from the Docker image.

The backend must not contain deployment-platform-specific business
logic. Deployment platforms are interchangeable as long as they support
the application runtime and required environment variables.

Initial deployment targets may include:

-   Render;
-   Railway;
-   Google Cloud Run;
-   other platforms compatible with the containerized FastAPI
    application.

Do not introduce platform-specific code or infrastructure unless a
deployment target is explicitly selected later.

### Docker requirements

-   slim Python base;
-   non-root user;
-   environment-driven configuration;
-   configurable `$PORT`;
-   reproducible dependency installation;
-   health-compatible HTTP startup.

Startup:

``` bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

The same startup command must work in a standard Python environment and
inside the Docker container.

SQLite is acceptable for the POC. Use PostgreSQL only if the system
later requires multi-instance persistence or the selected deployment
environment makes persistent local storage unsuitable.

Deployment configuration should therefore be kept separate from domain
and application logic so that moving from one hosting provider to
another does not require architectural changes.

## 22. Definition of Done

The engine is complete when:

-   it starts from a clean environment;
-   all tests pass;
-   at least one real connector works end-to-end;
-   additional enabled connectors either work or clearly report
    unavailable/not configured;
-   CV extraction produces a validated profile;
-   preferences become structured criteria;
-   offers normalize into the canonical model;
-   duplicates are removed conservatively;
-   filters work;
-   matching is deterministic and explainable;
-   LLM explanations are validated and grounded;
-   API returns a frontend-ready shortlist;
-   Docker build succeeds;
-   no secret is committed;
-   the final flow is demonstrable.

## 23. Explicitly out of scope

Do not implement:

-   browser automation;
-   automatic form submission;
-   CAPTCHA solving/bypass;
-   anti-bot bypass;
-   authentication bypass;
-   unauthorized scraping;
-   hiring prediction;
-   recruiter behavior prediction;
-   multi-agent architecture;
-   microservices;
-   RAG;
-   vector databases;
-   Kubernetes;
-   advanced ML training;
-   autonomous source discovery.

## 24. Final product flow

``` text
Candidate
  ↓
CV + preferences
  ↓
AI Agent
  ↓
Understand
  ↓
Search
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
Shortlist
  ↓
Candidate decides to apply
```
