# AI Job Search Agent backend

FastAPI modular monolith. The implemented search path is:

```text
POST /api/search → SearchCriteria → enabled connectors → RawOffer
                 → source normalizers → JobOffer → filtering → matching
                 → explanation → recommendation → ranking
```

Collection, normalization, filtering, matching, explanation, recommendation, and ranking remain separate services. Deduplication, LLM explanation, CV parsing, and application submission are not part of this path.

## Run locally

Use Python 3.12+, create a virtual environment, install `requirements.txt`, then run from this directory:

```sh
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Copy `.env.example` to `.env`. Configuration is read from environment variables. Application construction does not make network requests; HTTP requests occur only when an enabled connector is used by `POST /api/search`.

## Connector configuration

All sources are disabled by default.

| Source | Configuration | Current behavior |
|---|---|---|
| RemoteOK | `REMOTEOK_ENABLED=true`; optional `REMOTEOK_ENDPOINT` defaults to the documented `https://remoteok.com/api`. | Can be explicitly enabled. Lifecycle remains `development`; live response shape, request limits, and reuse conditions are not fully verified. Attribution requirements are not implemented as a UI because this backend returns JSON only. |
| Lever | `LEVER_ENABLED=true` and a required `LEVER_SITE`. | Can be explicitly enabled for that SITE using the global API origin. Lifecycle remains `access pending`; third-party use conditions, region choice, and pagination termination remain unresolved. |
| Greenhouse | No activation setting is provided. | Not composed: the repository has no production parser or normalizer. The API requires a board context and applicable usage authorization. |

`HIMALAYAS_ENABLED` is retained in settings for compatibility but no Himalayas connector is part of this task. Connector availability is returned in `meta.connectors`; a connector's lifecycle status is not a claim that it is operational. Connector failures are isolated and summarized in `meta.failedSources` without returning exception messages or raw payloads.

## Search routes

`POST /api/search` accepts the existing `profile` and `preferences` request shape. Search criteria are copied from preferences; the profile and preferences are used by the deterministic matching stage. Results are canonical `JobOffer` objects. `meta.sources` lists sources that returned normalized, retained offers.

Search now applies explicit post-retrieval filtering and deterministic matching. `results` contains offers that were not contradicted by a known `REQUIRED` criterion; unknown evidence does not exclude. The additive `matches` array contains an offer identity, filtering evidence, dimension scores, confidence, and a deterministic explanation. `excluded` contains offers rejected by a known required conflict and the evidence for that decision. Matching is not a hiring prediction and does not call the LLM. Exact weighting and missing-evidence behavior are documented in `docs/implementation/filtering-and-matching.md`.

Each retained match includes a deterministic `recommendation` decision. The `ranking` object orders only recommended offers, with explicit ranks and their canonical source provenance. `results` still includes every offer retained by filtering, even when recommendation says not to present it or evidence is insufficient. Defaults are configurable with `RECOMMENDATION_SCORE_THRESHOLD=60` and `RECOMMENDATION_MINIMUM_CONFIDENCE=0.5`; these are initial presentation-policy thresholds, not calibrated hiring estimates. The policy, decision reasons, order, and tie-break rules are documented in `docs/implementation/recommendation-and-ranking.md`.

`POST /api/search/from-text` remains `501 Not Implemented`: preference parsing depends on the LLM path and is outside this task. `GET /health` returns the health status.

## Shortlist

The backend persists a user-selected copy of a canonical `JobOffer` in SQLite. `POST /api/shortlist` accepts the offer object directly from `POST /api/search` results; it does not require or save matching/recommendation data. Duplicate stable offer identities return `409`. The entry starts at `SAVED`; use `PATCH /api/shortlist/{id}` with `{"status":"INTERESTED"}`, `APPLYING`, `APPLIED`, `REJECTED`, `ARCHIVED`, or `SAVED` to update it. `APPLIED` records the user's declaration only and never submits an application. `GET /api/shortlist`, `GET /api/shortlist/{id}`, and `DELETE /api/shortlist/{id}` list, retrieve, and remove saved entries.

`DATABASE_URL` defaults to `sqlite:///./job_agent.db`, resolved from the backend process working directory. SQLite creates the shortlist table on its first use. This MVP has no authentication: the database represents one shared local shortlist, not user-isolated data. File-backed SQLite is supported; database errors return `503` without revealing connection details. See `docs/implementation/shortlist.md` for identity rules and limitations.

Example request:

```json
{
  "profile": {},
  "preferences": {
    "jobTitles": ["Platform Engineer"],
    "countries": ["SN"],
    "skills": ["Python"]
  }
}
```

## Limitations and tests

No connector is declared operational. Tests use local fixtures and `httpx.MockTransport`; they do not contact job sources or establish permission to store or redistribute their data. Greenhouse remains unavailable until a source-specific parser and normalizer are implemented and authorized. Lever is opt-in only and currently maps a subset of its documented fields. RemoteOK is opt-in only and its output must be displayed with the required source and offer links before use as an aggregator.

Run all backend tests from this directory:

```sh
python -m pytest -q
```
