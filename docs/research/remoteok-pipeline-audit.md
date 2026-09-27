# RemoteOK pipeline audit

**Audit date:** 2026-09-27  
**Connector lifecycle:** `development`; the audit does not promote it.

## Pipeline findings

| Stage | Before audit | Finding / correction | After audit |
|---|---|---|---|
| API route and response | `IMPLEMENTED_AND_TESTED` | `/api/search` exposes retained canonical offers in `results`, retained per-offer evaluations in `matches`, known required conflicts in `excluded`, and only recommended offers in `ranking`. No response-contract change was needed. | `IMPLEMENTED_AND_TESTED` |
| Configuration and composition | `IMPLEMENTED_AND_TESTED` | Explicit `REMOTEOK_ENABLED` and endpoint settings construct the connector without a request. Invalid endpoints leave it inactive. `development` remains explicit. | `IMPLEMENTED_AND_TESTED` |
| RemoteOK collection and HTTP | `IMPLEMENTED_AND_TESTED` | Mocked HTTP tests cover feed metadata, raw payload/provenance, empty/invalid responses, timeouts, HTTP/auth/rate-limit errors, bounded transient retry, and source-failure isolation. Criteria are not translated into undocumented query parameters. | `IMPLEMENTED_AND_TESTED` |
| RemoteOK normalization | `PARTIALLY_IMPLEMENTED` | HTML descriptions were previously returned with markup and active script/style content. They are now reduced to readable text; script/style content is omitted. A numeric zero salary bound is now kept only in `RawOffer`, because its feed meaning is not established. | `IMPLEMENTED_AND_TESTED` |
| Canonical `JobOffer` | `IMPLEMENTED_AND_TESTED` | Source URL, offer URL, and application URL stay separate. Only `date` maps to `publishedAt`; unavailable dates/fields remain null, empty, or `UNKNOWN`. Tags remain categories and do not become skills. Remote eligibility, geography, salary currency/period, employment type, and seniority are not invented. | `IMPLEMENTED_AND_TESTED` |
| Deduplication | `IMPLEMENTED_AND_TESTED` | Deterministic exact source identity and canonical URL rules are tested. Cross-source matching requires exact company/title plus overlapping explicit location; same-company offers with different locations remain distinct. | `IMPLEMENTED_AND_TESTED` |
| Filtering | `IMPLEMENTED_AND_TESTED` | Only a known conflict on a `REQUIRED` criterion excludes. Unknown location, country, remote, seniority, contract, skills, timezone, or salary evidence remains unknown and does not exclude. | `IMPLEMENTED_AND_TESTED` |
| Matching and scoring | `IMPLEMENTED_AND_TESTED` | Deterministic weights remain skills 50%, preferences 25%, experience 15%, and role alignment 10%. Missing dimensions do not become positive evidence; effective evaluated weight is also the confidence measure. | `IMPLEMENTED_AND_TESTED` |
| Recommendation and ranking | `IMPLEMENTED_AND_TESTED` | `INSUFFICIENT_EVIDENCE` below confidence `0.5` is expected; ranking includes only included, recommended offers with a numeric score. The reported empty ranking is therefore not a propagation bug when no offer meets the confidence policy. | `IMPLEMENTED_AND_TESTED` |
| Full RemoteOK API path | `PARTIALLY_IMPLEMENTED` | Added a controlled fixture scenario and endpoint test using the task's exact profile and preference values. It checks deduplication, required-location exclusion, unknown-location retention, repeated score, recommendation, ranking, and metadata. | `IMPLEMENTED_AND_TESTED` |
| Visible attribution / retention authorization | `IMPLEMENTED_BUT_UNVERIFIED` | The API retains source and offer links, but no frontend/report HTML is present in this repository to prove required visible attribution. No blanket storage/retention permission or request quota was established by this audit. | `IMPLEMENTED_BUT_UNVERIFIED` |

## Response category contract

- `results`: every offer that survives filtering, in source order; this can include offers whose recommendation is `NOT_RECOMMENDED` or `INSUFFICIENT_EVIDENCE`.
- `matches`: the filter, deterministic score/evidence, explanation, and recommendation for each retained result.
- `excluded`: offers excluded only by an established conflict with a `REQUIRED` criterion, with the filtering and recommendation reason.
- `ranking`: only retained offers that pass the configured recommendation score and confidence policy.
- `meta.total` and `meta.sources`: describe retained `results`, not the raw number collected. Connector failures are listed in `meta.failedSources`.

## Reproducible fixture outcome

The endpoint integration test uses `backend/tests/fixtures/remoteok/poc_scenario.json` and the profile/preferences specified in the task. The fixture is synthetic and uses reserved `.invalid` links; it is not represented as a live RemoteOK response.

Assertions from the executed test:

- 4 raw entries become 3 unique offers after duplicate source ID `900001` is removed.
- Offer `900001` has the requested Dakar location, is retained, and has score `100` with confidence `0.35`. It is `INSUFFICIENT_EVIDENCE`, because tags are categories rather than proven skills and other matching dimensions are unavailable; it is not ranked.
- Offer `900002` has location `Berlin, Germany`; it is excluded for the known conflict with required location `Dakar`.
- Offer `900003` has no location; the required location assessment is `UNKNOWN`, not a conflict, so it remains in `results`.
- `meta.total` is `2`, `meta.sources` contains `RemoteOK`, `meta.failedSources` is empty, and the connector remains `development` and active for this explicitly enabled test runtime.
- Repeating the same fixture request yields the same matching score. The endpoint test also checks that the description is plain text, salary units stay unknown, and skills remain empty.
- A separate mocked endpoint test confirms a RemoteOK failure appears in `meta.failedSources` without discarding a valid result from another source.

This scenario demonstrates collection through API response and deterministic empty ranking under the current evidence threshold. It does not demonstrate a RemoteOK offer being confidently recommended; the observed source fields do not establish enough matching evidence under the unchanged policy.

## External source conditions checked

The official [Remote OK FAQ](https://remoteok.com/faq) documents the public JSON feed, shows tag filters, and instructs aggregators/public sharers to credit Remote OK and link original postings. The [Remote OK Terms](https://remoteok.com/legal), updated July 20, 2026 when checked, require a web or in-app link to Remote OK on the page/screen using API/site data. This is a source-document review, not legal advice or confirmation that Job Agent's storage/retention is authorized. The source documents consulted do not establish a request quota, pagination contract, or blanket storage/retention permission. No live endpoint request was made for this audit.

## Remaining work

- **Blocking lifecycle criteria:** user-facing attribution has not been verified in an available frontend; storage/retention and request limits remain unresolved. Keep lifecycle at `development` and use explicit opt-in.
- **Non-blocking data limits:** RemoteOK fields in the observed feed do not reliably supply country, eligibility, experience, employment type, seniority, timezone, or salary units for every offer. Matching confidence will remain low for many offers.
- **Manual external validation:** review source terms and any intended retention/redistribution with the responsible product/legal owner before production use. No live RemoteOK request or legal determination was made.
- **No report HTML:** no HTML report/template is present in the repository search; this audit therefore cannot validate external report presentation.
