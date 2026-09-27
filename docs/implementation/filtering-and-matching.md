# Deterministic filtering and matching (Task 7)

## Boundaries

`FilteringService` evaluates explicit `SearchCriteria` against a canonical
`JobOffer`. It returns one `FilteringResult` per offer and retains excluded
offers with their evidence. Only an explicit `REQUIRED` criterion with a
known `CONFLICT` excludes an offer. A missing field is `UNKNOWN`; it remains
eligible. Unspecified criterion strength defaults to `PREFERRED`. `PREFERRED`,
`OPTIONAL`, and `INFORMATIONAL` conflicts are reported but do not exclude.
List-valued title, location, country, company, skill, department, team, tag,
and keyword criteria use any-match semantics. Countries, skills, seniority,
employment type, and tags use normalized exact matching. Job-title comparison
is shared by filtering and matching: normalized exact titles are satisfied;
non-exact token overlap is partial evidence and remains `UNKNOWN`; no token
overlap is a conflict for a stated title preference. A shared generic word such
as “developer” does not satisfy a title preference. An unknown title does not
become a conflict. Partial title evidence can contribute a lexical similarity
score to matching, but does not become a satisfied criterion. Company/location
terms use normalized textual overlap. Keywords are checked against available
title, source summary, description, skills, and categories. These are
post-retrieval checks and do not claim that a source can search those fields.

Salary comparison is `UNKNOWN` unless the preference specifies both currency
and period and the offer contains comparable compensation with both units.
Comparable salary ranges satisfy when they overlap the requested range;
disjoint ranges conflict. No currency or pay period is inferred.

`MatchingService` accepts `UserProfile`, `SearchPreferences`, and `JobOffer`;
it has no connector, network, or LLM dependency. Text comparison uses Unicode
normalization, case folding, and deterministic token comparison. Skills score
is the percentage of listed offer skills present in the profile. Role
alignment is the maximum Jaccard overlap of title tokens across profile titles
and the offer title; non-exact overlap remains `UNKNOWN`. Experience score is 100 when the candidate meets the
offer's stated minimum; below it, the score is `100 * candidate years / minimum`
and the evidence is a conflict. The offer's maximum experience is not treated
as a hiring ceiling. The preferences dimension averages only explicit
preferences with comparable offer evidence; exact title matches score 100,
known mismatches score 0, and a partial title overlap contributes its Jaccard
similarity while remaining `UNKNOWN`. Missing or incomparable evidence is
excluded from that dimension average and remains listed as unknown.

Configured base weights are skills 0.50, preferences 0.25, experience 0.15,
and role alignment 0.10. Dimensions without a calculable score are omitted from
the final weighted average; the remaining base weights are renormalized to
sum to 1. `confidence` is the sum of the base weights of calculable dimensions
(0–1), independent of the score. When no dimension is calculable, score is
`null` and confidence is 0. Partial or zero lexical overlap is not by itself a
claim about a candidate's true ability; unavailable profile evidence remains
unknown. Scores are relevance measures, not probabilities of hiring.

`ExplanationService` copies structured filtering and matching states into
`MatchExplanation`, with fixed explanatory text. It does not recalculate the
score, inspect free-form text for instructions, or call an LLM. Matching data
is returned alongside a separate `OfferIdentity`; no matching fields are
added to canonical `JobOffer`.

## Search API

`POST /api/search` keeps the existing `results` key, now containing offers
retained by explicit required filtering. It adds:

- `matches`: offer identity, filtering evidence, deterministic `MatchingResult`,
  and structured explanation for retained offers;
- `excluded`: canonical offer plus filtering evidence, matching, and structured
  explanation for offers excluded by a known required conflict.

`meta.total` and `meta.sources` describe retained results. `meta.failedSources`
continues to describe collection failures. Additive `meta.normalizationFailures`
reports `totalRejected` and rejected counts in `bySource`; rejected payloads and
error text are not exposed. This API change is additive except that
`results` now excludes offers with a known required conflict. Unknown required
criteria do not exclude. `/api/search/from-text` parses explicit user
preferences with the configured structured LLM adapter and then uses the same
criteria builder and search pipeline; it does not persist parsed preferences.
See `natural-language-search.md` for its request and error behavior.
