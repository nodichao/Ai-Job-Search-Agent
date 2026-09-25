# Processing and Recommendation

**Status:** Draft for MVP / PoC  
**Scope:** Post-normalization processing of `JobOffer` objects through shortlist generation.

---

## 1. Purpose

This document defines how normalized `JobOffer` objects are processed after source-specific normalization until a final shortlist of relevant opportunities is produced.

The pipeline separates four different concerns:

1. **Deduplication** — remove multiple representations of the same opportunity.
2. **Filtering** — evaluate explicit search constraints.
3. **Matching** — measure how well the user profile corresponds to an offer.
4. **Explanation and Recommendation** — make the result understandable and determine which offers should be presented in the shortlist.

The MVP deliberately keeps matching simpler than a full HR assessment system. Advanced candidate-job fit based on detailed evidence from the candidate's career history is considered a future evolution.

---

## 2. Position in the Architecture

The processing pipeline begins after source data has been normalized into the canonical `JobOffer` model.

```text
RawOffer
   ↓
Normalizer
   ↓
JobOffer[]
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
```

The broader architecture is:

```text
UserProfile / SearchPreferences
              ↓
        SearchCriteria
              ↓
       SourceCapabilities
              ↓
     Source-specific Query
              ↓
          Connector
              ↓
           RawOffer
              ↓
          Normalizer
              ↓
          JobOffer[]
              ↓
       Processing Pipeline
              ↓
          Shortlist
```

---

# 3. Core Principles

### 3.1 Separate the questions

Each stage answers a different question.

| Stage | Question |
|---|---|
| Deduplication | Is this the same job opportunity as another result? |
| Filtering | Does this offer satisfy the user's explicit search criteria? |
| Matching | How well does the user's profile correspond to this offer? |
| Explanation | Why does the offer receive this result? |
| Recommendation | Should this offer be presented as a relevant opportunity? |
| Shortlist | What are the final offers presented to the user? |

These responsibilities must not be collapsed into a single operation.

### 3.2 Unknown is not the same as conflict

If an offer does not provide enough information to verify a criterion, the system must not automatically interpret the criterion as unsatisfied.

```text
SATISFIED ≠ UNKNOWN ≠ CONFLICT
```

Example:

```text
User salary preference: ≥ $1,500
Offer salary: not disclosed

Result: UNKNOWN
```

This is different from:

```text
User salary preference: ≥ $1,500
Offer salary: $1,000

Result: CONFLICT
```

### 3.3 Preferences and mandatory constraints must remain distinguishable

A user may express:

- a mandatory requirement;
- a strong preference;
- a simple preference;
- information that is useful but non-decisive.

A preference should not automatically become a blocking constraint.

For example:

```text
Remote = REQUIRED
```

is different from:

```text
Remote = PREFERRED
```

This distinction affects filtering and recommendation.

### 3.4 The system must not claim more certainty than the data supports

The agent can identify relevant opportunities and explain the basis of its assessment.

It must not claim that a candidate will be contacted, interviewed, or hired.

Similarly, a shortlist means:

> offers considered sufficiently relevant to be presented to the user as opportunities to consider.

It does not constitute a guarantee of eligibility or hiring.

---

# 4. Deduplication

## 4.1 Responsibility

Deduplication identifies multiple representations of the same job opportunity and prevents the same opportunity from appearing several times in the result set.

```text
JobOffer[]
    ↓
Deduplication
    ↓
Unique JobOffer[]
```

Deduplication is an independent processing step.

It is not part of:

- the connector;
- the normalizer;
- filtering;
- matching.

## 4.2 MVP rules

The MVP uses conservative rules.

### Level 1 — Exact source identity

```text
source.name + identity.sourceId
```

If the same source identifies the same offer with the same source identifier, it is a duplicate.

### Level 2 — Normalized offer URL

If two offers resolve to the same normalized offer URL, they can be treated as duplicates.

### Level 3 — Cross-source conservative comparison

When source identity differs, compare combinations such as:

- company;
- title;
- location.

Cross-source deduplication must remain conservative because two apparently similar offers may still represent distinct positions.

Description similarity can be introduced later.

## 4.3 Output

The deduplication service receives:

```text
JobOffer[]
```

and returns:

```text
Unique JobOffer[]
```

No deduplication metadata is required inside `JobOffer` for the MVP.

---

# 5. Filtering

## 5.1 Responsibility

Filtering evaluates whether an offer corresponds to the user's explicit search criteria.

```text
SearchCriteria + JobOffer
             ↓
          Filtering
             ↓
      Relevant / Excluded
```

Filtering answers:

> "Does this offer correspond to what the user is looking for?"

It does not determine how well the candidate matches the employer's requirements.

## 5.2 Searchable versus post-retrieval criteria

A criterion may be:

1. directly supported by a source query;
2. unavailable as a source-side filter but available after normalization;
3. semantic and better handled by matching.

Therefore:

```text
Source filtering
       +
Post-retrieval filtering
       +
Matching
```

must remain conceptually distinct.

## 5.3 Hard constraints

Explicit mandatory constraints can exclude an offer when the offer provides sufficient evidence of a conflict.

Examples:

```text
Remote required
Offer = on-site only

→ CONFLICT
→ Exclude
```

But:

```text
Remote required
Offer = work mode not specified

→ UNKNOWN
```

must not automatically become a conflict.

## 5.4 Preference strength

Filtering must respect the strength of the user's preference.

Conceptually:

```text
REQUIRED
PREFERRED
OPTIONAL
INFORMATIONAL
```

A `REQUIRED` criterion can be blocking.

A `PREFERRED` criterion should normally influence matching or recommendation rather than automatically exclude an offer.

---

# 6. Matching

## 6.1 Responsibility

Matching evaluates the correspondence between the user's profile and the job offer.

It answers:

> "How well does this candidate profile correspond to this offer?"

This is different from filtering.

Filtering is primarily:

```text
User intent → Offer
```

Matching is primarily:

```text
User profile → Offer requirements
```

## 6.2 MVP scope

For the proof of concept, matching should remain focused and explainable.

Initial dimensions may include:

- role / position;
- relevant skills;
- experience;
- seniority;
- location / remote compatibility;
- employment type;
- other structured profile criteria available in the MVP.

The exact scoring weights should be defined during implementation/testing rather than treated as universal truths.

## 6.3 MatchingResult

Conceptual MVP structure:

```text
MatchingResult
├── score
├── dimensions[]
├── matchedCriteria[]
├── missingCriteria[]
├── conflicts[]
└── confidence
```

### `score`

A normalized indication of the degree of correspondence.

The score is not a probability of being hired or contacted.

### `dimensions`

Breakdown of the main matching dimensions.

Example:

```text
skills       → strong
experience   → strong
role         → strong
remote       → compatible
```

### `matchedCriteria`

Important elements of the offer that correspond to the user's profile.

### `missingCriteria`

Requirements or desirable elements that are not found in the available profile information.

A missing criterion must not automatically mean that the candidate does not possess it.

### `conflicts`

Known incompatibilities between the profile and the offer.

### `confidence`

Indicates how well supported the matching assessment is by available data.

This is distinct from the match score.

---

# 7. Matching and Advanced Candidate-Job Fit

The MVP should not attempt to build a complete HR assessment engine.

A more advanced future version can move beyond keyword or structured-field matching toward evidence-based candidate-job fit.

For example:

```text
Job requirement:
"Experience managing a development team"

Candidate evidence:
"Led a team of 5 developers on a production project"
```

This future system could consider:

- concrete evidence of skill use;
- depth of experience;
- scope of responsibility;
- sector/context;
- qualifications;
- management experience;
- career coherence.

This is valuable because:

```text
keyword similarity
        ≠
real candidate-job fit
```

However, this level of analysis is outside the core MVP.

The MVP should establish the architecture so that this capability can be added later without changing the source connectors or canonical `JobOffer` model.

---

# 8. Explanation

## 8.1 Responsibility

Explanation makes the result of filtering, matching, and recommendation understandable to the user.

It answers:

> "Why was this offer considered relevant, and what are the important gaps or uncertainties?"

Explanation should not independently recalculate the matching score.

Conceptually:

```text
MatchingResult
      +
Relevant filtering information
      ↓
Explanation
```

## 8.2 Example

```text
Match score: 87%

Strong matches:
✓ React
✓ Node.js
✓ Full-Stack role
✓ 3+ years experience
✓ Remote

Points to verify:
⚠ Salary not disclosed
⚠ AWS experience not identified
```

The explanation must distinguish:

- matched information;
- missing information;
- known conflicts;
- unknown information.

---

# 9. Recommendation

## 9.1 Responsibility

Recommendation combines the results of the previous stages to determine which opportunities should be presented to the user.

It answers:

> "Is this offer sufficiently relevant to be presented as an opportunity to consider?"

Recommendation is therefore different from matching.

```text
Matching
→ measures correspondence

Recommendation
→ uses that assessment to determine presentation priority
```

## 9.2 Recommendation must not overclaim

The system should not state:

> "You will be selected."

or:

> "You are guaranteed to be eligible."

Instead:

> "This offer appears relevant based on the available information."

The final application decision remains with the user.

## 9.3 Conceptual RecommendationResult

```text
RecommendationResult
├── decision
├── priority
├── reasons[]
└── warnings[]
```

The precise recommendation taxonomy is intentionally left open for the MVP until matching behavior has been tested.

---

# 10. Shortlist

The shortlist is the final collection of offers that the agent presents to the user as relevant opportunities to consider.

```text
All retrieved offers
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
```

A shortlist is therefore **not**:

> "The list of jobs for which the candidate is guaranteed to be eligible."

It is:

> "The list of opportunities that the system considers sufficiently relevant to present to the user."

Example:

```text
SHORTLIST

1. Full-Stack Developer — Company A
   Match: 91%
   ✓ React
   ✓ Node.js
   ✓ Remote
   ✓ Experience aligned

2. React Developer — Company B
   Match: 84%
   ✓ Strong skill alignment
   ⚠ Salary not disclosed

3. Software Engineer — Company C
   Match: 78%
   ✓ Role compatible
   ⚠ AWS experience not identified
```

The user can then inspect the offer and decide whether to apply.

---

# 11. End-to-End Flow

```text
                    JobOffer[]
                        │
                        ▼
               ┌────────────────┐
               │ Deduplication  │
               └───────┬────────┘
                       │
                       ▼
                Unique JobOffers
                       │
                       ▼
               ┌────────────────┐
               │   Filtering    │◄──── SearchCriteria
               └───────┬────────┘
                       │
                       ▼
               Relevant Offers
                       │
                       ▼
               ┌────────────────┐
               │    Matching    │◄──── UserProfile
               └───────┬────────┘
                       │
                       ▼
                MatchingResult
                       │
                       ▼
               ┌────────────────┐
               │  Explanation   │
               └───────┬────────┘
                       │
                       ▼
               ┌────────────────┐
               │ Recommendation │
               └───────┬────────┘
                       │
                       ▼
                   Shortlist
                       │
                       ▼
               User reviews offers
                       │
                       ▼
                  User applies
```

---

# 12. Responsibility Boundaries

| Component | Must do | Must not do |
|---|---|---|
| Deduplication | Remove duplicate opportunities | Decide relevance |
| Filtering | Apply explicit search constraints | Evaluate candidate quality |
| Matching | Measure profile ↔ offer correspondence | Guarantee hiring |
| Explanation | Explain assessment | Invent missing information |
| Recommendation | Select relevant opportunities for presentation | Decide for the user |
| Shortlist | Present final opportunities | Guarantee eligibility |

---

# 13. MVP Boundaries

The proof of concept prioritizes:

```text
✓ Multi-source aggregation
✓ Canonical JobOffer model
✓ Deduplication
✓ Explicit filtering
✓ Explainable profile/offering matching
✓ Shortlist generation
✓ Direct access to application destination
```

The PoC does not attempt to fully implement:

```text
✗ Hiring probability prediction
✗ Recruiter behavior prediction
✗ Complete HR candidate assessment
✗ Deep career-context inference
✗ Guaranteed eligibility assessment
✗ Automated application without explicit user control
```

These capabilities may be introduced later.

---

# 14. Future Evolution

The processing architecture is designed to evolve toward a richer candidate-job fit engine:

```text
                    Current MVP
                        │
                        ▼
              Structured Matching
                        │
                        ▼
               Evidence Extraction
                        │
                        ▼
             Candidate-Job Fit
                        │
                        ▼
             Confidence Assessment
                        │
                        ▼
            More precise Recommendation
```

The future engine could analyze not only whether a skill appears in a CV, but whether the available profile contains credible evidence that the candidate has actually practiced that skill in a relevant context.

This evolution must not require changing:

- source connectors;
- source-specific query builders;
- `RawOffer`;
- the canonical `JobOffer` model.

---

# 15. Final Architectural Principle

The processing pipeline must preserve the following separation:

```text
Deduplication
    ↓
"Is it the same opportunity?"

Filtering
    ↓
"Does it match what I am looking for?"

Matching
    ↓
"How well does my profile correspond to it?"

Explanation
    ↓
"Why did the system reach this assessment?"

Recommendation
    ↓
"Should this opportunity be presented to me?"

Shortlist
    ↓
"The opportunities presented for my consideration."
```

The purpose of the agent is not to decide which jobs the user must apply to.

Its purpose is to reduce the friction between **job discovery and relevant application** by transforming a large, heterogeneous set of offers into a smaller, explainable and actionable shortlist.
