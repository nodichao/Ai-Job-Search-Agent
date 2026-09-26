# Recommendation and ranking (Task 8)

## Service boundaries

- `FilteringService` evaluates explicit search criteria and determines
  inclusion. A known conflict excludes only when the criterion is `REQUIRED`.
- `MatchingService` computes deterministic relevance score, dimension evidence,
  and confidence. Score and confidence are separate quantities.
- `ExplanationService` presents the structured filter and match evidence.
- `RecommendationService` applies a configurable presentation policy to the
  filtering and matching results. It does not edit either result or `JobOffer`.
- `RankingService` orders only retained, recommended offers. It has no network
  or LLM dependency.

No recommendation, matching score, or ranking data is stored in `JobOffer`.
The ranking projection includes the canonical offer so its identity and source
provenance remain available to the caller.

## Recommendation policy

The architecture intentionally leaves recommendation categories and thresholds
open. Task 8 introduces a small explicit default policy, adjustable through
`RECOMMENDATION_SCORE_THRESHOLD` (default `60`, range 0–100) and
`RECOMMENDATION_MINIMUM_CONFIDENCE` (default `0.5`, range 0–1). The score
threshold requires a majority-level relevance score before presentation. The
confidence floor requires evidence covering at least half of the configured
matching weight; it is not a second score and does not increase the score.
These are initial product-policy defaults, not empirically calibrated values.

Decision order:

1. A filtered-out offer is `NOT_RECOMMENDED`, regardless of its score.
2. An included offer with `score=null` is `INSUFFICIENT_EVIDENCE`.
3. An included offer below the confidence floor is `INSUFFICIENT_EVIDENCE`,
   even if its available-dimension score is high.
4. Otherwise, a score at or above the threshold is `RECOMMENDED`; a lower score
   is `NOT_RECOMMENDED`.

Each result contains a stable reason code, plain explanation, and relevant
structured evidence. Unknown filtering and matching evidence appears as
warnings; unknown is never converted to a conflict. Existing matching conflicts
are also surfaced as warnings and are not treated as automatic hiring
judgments. These decisions concern presentation relevance only and do not
predict hiring, eligibility, contact, or application outcomes.

## Ranking

`RankingService` accepts recommendation candidates and returns only offers
that both pass filtering, have `RECOMMENDED` decisions, and have a numeric
matching score. Ordering is:

1. matching score descending;
2. matching confidence descending, but only as a tie-break after equal scores;
3. source name ascending, case-insensitive;
4. source ID, then canonical ID, then slug ascending;
5. offer URL ascending;
6. company name and position title ascending;
7. original input order as the final tie-break for otherwise identical keys.

Ranking never changes the matching score and never promotes `null` to zero.
Excluded, not-recommended, and insufficient-evidence offers are not ranked.
Repeated calls with the same ordered input produce the same result. Exact
duplicate ranking keys retain their input order because there is no
independent identity evidence with which to distinguish them.

## API

`POST /api/search` keeps `results`, `matches`, `excluded`, and `meta`.
`matches` adds a separate `recommendation` object for every retained offer.
`excluded` adds its `NOT_RECOMMENDED` decision. A new `ranking` object contains
`total` and rank-numbered recommended offers. Each ranked entry carries its
canonical `offer`, separate recommendation, score, and confidence. `results`
continues to contain every offer retained by filtering in source order; it is
not silently limited to recommended offers. `meta.total` and `meta.sources`
continue to describe those retained results.

## Limits and non-goals

Default thresholds have not been calibrated against user feedback or outcome
data. Scores rely on the deterministic lexical and structured comparisons
documented for Task 7. Recommendation does not establish source authorization,
candidate eligibility, or hiring likelihood. There is no LLM, final shortlist
persistence, application submission, browser automation, or connector change
in this task.
