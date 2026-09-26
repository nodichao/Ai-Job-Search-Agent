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
