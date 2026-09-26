# RemoteOK — Task 12 verification

**Checked:** 2026-09-26  
**Lifecycle:** `development` (explicit opt-in; not operational)

This addendum records a current official-source review and one read of the official JSON endpoint. Technical accessibility and the documented conditional attribution requirements are recorded separately from permission to store or redistribute job data.

## Official sources consulted

- Remote OK [FAQ — feeds, filters, and aggregators](https://remoteok.com/faq): documents the JSON feed URL, says the public feeds require no authentication, gives `tag` and `tags` examples, and asks aggregators/public feed sharers to name Remote OK and link each original job post.
- Remote OK [Terms of Service](https://remoteok.com/legal): requires a web or in-app hyperlink to Remote OK on the page or screen where API/site data is used. The API response's current legal notice additionally asks for a followed link to the original URL, source credit, and excludes use of the Remote OK logo without written permission.
- Official [JSON feed](https://remoteok.com/api): fetched once for schema inspection. The observed body was a JSON array whose first element contained `last_updated` and `legal`, followed by job objects. Observed job properties included `id`, `slug`, `epoch`, `date`, `company`, `company_logo`, `position`, `tags`, `description`, `location`, `apply_url`, `salary_min`, `salary_max`, and `url`.

The field list and leading metadata object are observations from the endpoint response, not a published schema guarantee. The response may change. No pagination or request quota was stated in the consulted official documentation. Although `tag` and `tags` query filters are documented, no mapping from the application's generic `SearchCriteria` fields to those parameters has been established, so the connector sends no such parameters.

### Technical requirements

- **Endpoint/method/format:** `GET https://remoteok.com/api`, JSON feed.
- **Authentication/headers:** the FAQ says the public feed requires no authentication. No mandatory custom request header is documented in the consulted sources.
- **Filters/pagination:** `tag` and `tags` are shown by the FAQ; the connector does not infer or send them. Pagination is not documented.
- **Frequency/rate limits:** no quota or request frequency is stated in the consulted sources. The regular shared client has bounded retries for transient failures and does not retry HTTP 429; the optional diagnostic script makes one attempt.

### Usage requirements

- **Attribution/links:** name Remote OK as the source and link each original job URL for aggregator/public-feed use. Link back to Remote OK from the page or app screen that uses API data. The current feed legal notice asks for a followed original URL and disallows use of the Remote OK logo without written permission.
- **Aggregation:** the FAQ explicitly describes aggregator/public sharing with those attribution conditions.
- **Storage, retention, redistribution/commercial scope:** no blanket permission or retention rule was found in the consulted sources. These remain unresolved for Job Agent.

## Code behavior verified and adjusted

- The configured endpoint defaults to the official `https://remoteok.com/api` and the connector remains disabled by default (`REMOTEOK_ENABLED=false`). Application composition performs no HTTP request.
- The connector validates the JSON list, recognizes and validates the observed leading feed metadata, skips it as a non-job, and preserves its timestamp and legal notice in each `RawOffer.provenance`. It preserves each job object as `RawOffer.payload`.
- The normalizer continues to map only source fields that exist: `url` to `identity.offerUrl`, `apply_url` to `application.applyUrl`, `date` to `publishedAt`, `position` to title, tags to categories, and provided company/location/salary values to their canonical fields. It does not infer remote eligibility, salary currency/period, or unsupported criteria.
- The common HTTP layer applies the configured timeout and bounded retries for transient network/server errors. It does not retry authorization errors or HTTP 429. Error paths and retry behavior are covered with mocked HTTP; they were not induced against the live source.
- The search runtime reports `development`, including when explicitly enabled. A successful request does not promote the connector lifecycle.

## Usage conditions and unresolved items

**Documented:** Remote OK describes its public feed as free and unauthenticated. It explicitly gives conditional instructions for aggregators: identify Remote OK as the source and link each original offer. Its terms require a Remote OK hyperlink on the page/screen using the data; the feed's current legal notice asks for a followed offer link. Do not use the Remote OK logo without written permission.

**Not established:** the documentation does not specify request quotas, pagination, retention/storage duration, or a blanket authorization for this project's ongoing storage or downstream redistribution. The backend returns source name and source/offer URLs, but there is no UI here to enforce visible, followed attribution. A consuming client must implement those links and credit before using results as an aggregator. These conditions prevent an `operational` lifecycle designation.

## Live request record

The official endpoint page was read once through the research browser on 2026-09-26 to inspect the current response envelope and metadata. No raw response was added as a repository fixture. No request was made through the backend connector or `/api/search`; no live offer was saved to SQLite. The automated tests use fixtures and mocked transports only.

Do not run a connector search against the live feed from CI or automatically at startup. Keep the connector disabled unless an operator deliberately opts in, and ensure the consuming UI meets the documented attribution requirements before using the results. A request's success is evidence of technical access only.

If a developer elects to perform a single technical retrieval check, run `python -m scripts.remoteok_smoke --confirm-one-off-read` from `backend/`. It makes one GET with retries disabled, normalizes in memory, and reports only counts. It is not part of tests or CI. The script was not run as part of this task because downstream attribution and data retention conditions for the actual application remain unresolved.
