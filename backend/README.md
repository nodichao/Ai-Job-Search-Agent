# AI Job Search Agent backend

Modular-monolith backend for the AI Job Search Agent. The current vertical implements the RemoteOK JSON collection boundary (`SearchCriteria` → `RawOffer`) and a separate source normalizer (`RawOffer` → canonical `JobOffer`). It does not run matching, scoring, recommendations, CV parsing, or LLM operations.

## Run locally

Use Python 3.12+, create a virtual environment, install `requirements.txt`, then run from this directory:

```sh
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Copy `.env.example` to `.env` and set environment variables as needed. No secret is committed. `GET /health` returns `{"status":"ok"}`. The generic `ConnectorBinding` used by `SearchService` receives `REMOTEOK_ENABLED` as its `enabled` value when the app composes a connector. The app does not construct one automatically because the project references do not specify the RemoteOK JSON endpoint. After supplying a verified endpoint, composition can use `SearchService([ConnectorBinding(remoteok_connector, enabled=settings.remoteok_enabled)])`.

## RemoteOK vertical

`RemoteOKConnector` requires an endpoint to be injected explicitly. The project documents a public JSON feed and its observed fields, but does not record the exact endpoint URL or top-level response envelope. The current adapter accepts a JSON array of objects and rejects other shapes; confirm that envelope against an authorized endpoint before live use. It accepts `SearchCriteria` and deliberately sends no query parameters: dedicated search parameters and pagination behavior are not verified. The connector preserves source payloads and provenance in `RawOffer`; `RemoteOKNormalizer` performs the separate mapping to `JobOffer`.

The source research says public JSON access does not require authentication, requires attribution, and requires a RemoteOK link. That does not establish permission for aggregation, storage, or redistribution. The implementation keeps this vertical in memory and does not add persistence. It does not infer an offer's `remote` eligibility from the source's overall remote-job scope. Tags are retained as categories because their precise skills taxonomy is not established. Salary currency, period, and type remain unknown. `epoch`, dates other than an ISO-formatted `date`, and pagination are not interpreted. Non-ISO or absent `date` values remain unknown.

## Tests

Run `pytest` from this directory. RemoteOK connector and pipeline tests use local JSON fixtures and `httpx.MockTransport`; no test contacts RemoteOK.

## Lever vertical

`LeverConnector` requires an explicit company `SITE`; it requests that site's postings and does not turn `SearchCriteria` into undocumented filters. It uses the documented `skip`, `limit`, and `mode=json` parameters, a configurable page size (default 20, as in the task-provided example), and the shared result cap. The shared paginator stops on an empty or short page and enforces the cap; the precise source-side termination convention and the default page size are not established by project research and should be verified before relying on exhaustive live collection. The configured `https://api.lever.co` host comes from the task-provided URL example, not the project reference documents.

`LeverNormalizer` maps documented `id`, `text`, and category values only. `allLocations` and `location` are retained as location strings; `commitment` is mapped only for recognized employment types; team and department are preserved. No remote eligibility, summary, compensation, offer URL, apply URL, or dates are inferred. The company name is optional context supplied by the caller. Public endpoint access does not by itself establish permission for aggregation, storage, redistribution, or application automation; source terms still require verification.

## Greenhouse status

Project references do not establish the Greenhouse board endpoint shape or response schema. `GreenhouseConnector` therefore requires an explicit board context, endpoint, and parser; it is a transport boundary only. The injected parser contract can create `RawOffer` values, but no built-in Greenhouse schema parser or `JobOffer` normalizer is claimed. The opaque fixture and test parser exercise dependency boundaries only; they do not represent a verified API response. Confirm the endpoint, schema, pagination, and applicable terms before configuring a real source.

Run `pytest` from this directory. Lever, Greenhouse, and RemoteOK tests use local JSON fixtures and `httpx.MockTransport`; no test contacts these services. Greenhouse's test parser is synthetic because the project has no verified response schema.
