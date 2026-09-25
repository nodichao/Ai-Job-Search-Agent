# Functional Architecture — Discovery & Suggestion

**Status:** MVP / PoC architecture  
**Scope:** Part 1 of the Job Search Agent — from user registration/profile setup to the shortlist and the user's explicit decision to apply.

---

## 1. Purpose

This document defines the functional architecture of **Part 1** of the Job Search Agent.

Part 1 is responsible for transforming:

```text
User profile + search intent
            ↓
      Job discovery
            ↓
      Offer processing
            ↓
      Offer evaluation
            ↓
      Relevant shortlist
            ↓
      User decision
```

The workflow ends when the user explicitly decides to apply:

```text
POSTULER
```

The application workflow itself belongs to **Part 2** and is defined separately in `application-workflow.md`.

---

# 2. Functional Boundary

The functional boundary is:

```text
PART 1 — DISCOVERY & SUGGESTION

Registration
    ↓
UserProfile
    ↓
SearchPreferences
    ↓
SearchCriteria
    ↓
Search & Discovery
    ↓
Collection
    ↓
Normalization
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
    ↓
USER DECIDES
"POSTULER"

─────────────────────────────────────

PART 2 — APPLICATION WORKFLOW
```

Part 2 starts only after the user's explicit decision to apply.

---

# 3. Functional Objective

The objective of Part 1 is to reduce the friction involved in finding relevant job opportunities.

The system should transform a large and heterogeneous set of job offers into a smaller, explainable and actionable shortlist.

The system does **not** attempt in the MVP to:

- guarantee that a candidate will be contacted;
- predict hiring decisions;
- guarantee eligibility for a job;
- replace the user's final decision to apply.

The purpose is to help the user identify opportunities worth considering.

---

# 4. High-Level Functional Architecture

```text
                         USER
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
       User & Profile            Search Preferences
        Management                     │
             │                         ▼
             │                  Search Criteria
             │                         │
             │                         ▼
             │                Search & Discovery
             │                         │
             │                         ▼
             │                    Job Offers
             │                         │
             │                         ▼
             │                Offer Processing
             │                         │
             │              ┌──────────┴──────────┐
             │              │                     │
             │              ▼                     ▼
             │       Deduplication            Filtering
             │              │                     │
             │              └──────────┬──────────┘
             │                         ▼
             │                     Matching
             │                         │
             └─────────────────────────┤
                                       ▼
                                  Explanation
                                       │
                                       ▼
                                  Recommendation
                                       │
                                       ▼
                                   Shortlist
                                       │
                                       ▼
                               USER DECISION
                                       │
                                  "POSTULER"
                                       │
                                       ▼
                              PART 2 — APPLICATION
```

---

# 5. Functional Modules

## 5.1 User & Profile Management

### Responsibility

Manage the information that represents the candidate and can be used later for search, matching and application preparation.

### Main concept

```text
UserProfile
```

The profile may contain information such as:

```text
UserProfile
├── professional identity
├── skills
├── experience
├── education
├── languages
├── location
├── certifications
├── projects
└── documents
```

The profile is a persistent representation of the candidate.

### Functional question

> **Who is the candidate?**

---

# 6. Search Preferences

## Responsibility

Capture what the user is currently looking for.

Search preferences represent **user intent**, not necessarily the complete professional profile.

Examples include:

```text
Desired roles
Location
Remote preference
Employment type
Salary preference
Experience range
Industries
Other job preferences
```

A preference may have a different level of importance.

Conceptually:

```text
REQUIRED
PREFERRED
OPTIONAL
INFORMATIONAL
```

This distinction is important because a preference should not automatically behave like a blocking constraint.

### Functional question

> **What is the user looking for?**

---

# 7. Search Criteria

`SearchCriteria` is the executable representation of the current search intent.

```text
SearchPreferences
        ↓
SearchCriteria
```

It provides the criteria that can be translated into source-specific searches and/or evaluated after retrieval.

### Functional responsibility

Transform user intent into a source-independent search representation.

```text
SearchCriteria
├── roles
├── skills
├── locations
├── remote
├── employment types
├── salary
├── seniority
└── other supported criteria
```

Not every criterion is necessarily searchable on every source.

The system must rely on `SourceCapabilities` to determine how each source can use a criterion.

---

# 8. Search & Discovery

## Responsibility

Find job opportunities across the selected heterogeneous sources.

```text
SearchCriteria
        ↓
SourceCapabilities
        ↓
Source-specific Query
        ↓
Connectors
        ↓
RawOffers
```

The architecture must not assume that all sources expose the same search capabilities.

For example:

```text
Himalayas
→ structured job search

RemoteOK
→ source-specific public data retrieval

Lever
→ company/job-board-specific context
```

Therefore, the generic search intent is translated into source-specific operations.

### Functional question

> **Where are the opportunities matching the user's search intent?**

---

# 9. Collection and Normalization

## 9.1 Collection

Connectors retrieve source data and produce `RawOffer` objects.

```text
Source
  ↓
Connector
  ↓
RawOffer
```

`RawOffer` preserves the source representation and provenance.

## 9.2 Normalization

The source-specific normalizer transforms each `RawOffer` into the canonical `JobOffer`.

```text
RawOffer
   ↓
Normalizer
   ↓
JobOffer
```

The purpose is to make offers from different sources comparable in the rest of the pipeline.

```text
Himalayas RawOffer ─┐
RemoteOK RawOffer ──┼→ Normalization → JobOffer
Lever RawOffer ─────┤
Other RawOffer ─────┘
```

The canonical `JobOffer` model is source-independent.

---

# 10. Deduplication

## Responsibility

Prevent the same opportunity from appearing multiple times.

```text
JobOffer[]
    ↓
Deduplication
    ↓
Unique JobOffer[]
```

The central question is:

> **Are these representations the same job opportunity?**

The MVP uses conservative deduplication:

1. source identity;
2. normalized offer URL;
3. conservative cross-source comparison using company, title and location.

Deduplication must not be confused with filtering or matching.

---

# 11. Filtering

## Responsibility

Evaluate whether an offer satisfies the user's explicit search criteria.

```text
SearchCriteria + JobOffer
             ↓
          Filtering
             ↓
      Relevant / Excluded
```

The central question is:

> **Does this offer correspond to what the user is looking for?**

Filtering may occur through:

- source-side search parameters;
- post-retrieval filtering;
- explicit hard constraints.

## Important distinction

```text
SATISFIED
UNKNOWN
CONFLICT
```

An unknown value must not automatically be treated as a conflict.

Example:

```text
Salary preference: ≥ $1,500
Offer salary: not disclosed

→ UNKNOWN
```

This is different from:

```text
Offer salary: $1,000

→ CONFLICT
```

Similarly, a preferred condition is not automatically a blocking constraint.

---

# 12. Matching

## Responsibility

Evaluate the correspondence between the user's profile and the job offer.

The central question is:

> **How well does this candidate profile correspond to this offer?**

Conceptually:

```text
UserProfile
     +
JobOffer
     ↓
Matching
     ↓
MatchingResult
```

## MVP dimensions

The MVP may evaluate dimensions such as:

```text
Role
Skills
Experience
Seniority
Location / Remote
Employment type
Other structured profile criteria
```

The matching result may contain:

```text
MatchingResult
├── score
├── dimensions
├── matchedCriteria[]
├── missingCriteria[]
├── conflicts[]
└── confidence
```

### Score

The score represents the degree of correspondence.

It is **not**:

- a probability of being hired;
- a probability of being contacted;
- a guarantee of eligibility.

### Unknown information

A missing element in the available profile or offer data should not automatically be interpreted as absence.

```text
Unknown ≠ Missing skill
Unknown ≠ Conflict
```

---

# 13. Advanced Candidate–Job Fit

The MVP intentionally does not attempt to reproduce a complete HR assessment.

A future matching engine could move from simple structured/semantic correspondence toward evidence-based candidate-job fit.

Example:

```text
Requirement:
"Experience managing a development team"

Candidate evidence:
"Led a team of 5 developers on a production project"
```

Future analysis could consider:

- evidence of actual skill use;
- depth of experience;
- scope of responsibility;
- sector/context;
- qualifications;
- management experience;
- career coherence.

This is an evolution of the Matching module, not a separate Part 1 workflow.

The architecture must allow this future evolution without changing the source connectors or canonical `JobOffer` model.

---

# 14. Explanation

## Responsibility

Make the filtering/matching/recommendation result understandable to the user.

The central question is:

> **Why is this offer considered relevant, and what are the important gaps or uncertainties?**

Conceptually:

```text
MatchingResult
      +
Filtering information
      ↓
Explanation
```

Example:

```text
Match score: 87%

Strong matches:
✓ React
✓ Node.js
✓ Full-Stack role
✓ Experience aligned
✓ Remote

Points to verify:
⚠ Salary not disclosed
⚠ AWS experience not identified
```

The explanation must not invent information that is absent from the profile or offer.

---

# 15. Recommendation

## Responsibility

Determine whether an offer is sufficiently relevant to be presented to the user as an opportunity to consider.

The central question is:

> **Should this offer be presented to the user?**

Recommendation uses the results of:

- filtering;
- matching;
- explanation-related information.

Conceptually:

```text
FilteringResult
      +
MatchingResult
      ↓
Recommendation
```

The recommendation must not be interpreted as:

> "The candidate will get this job."

It is a product-level decision about **relevance and presentation**, not hiring prediction.

---

# 16. Shortlist

The shortlist is the final set of opportunities presented to the user after processing.

```text
All offers
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
SHORTLIST
```

The shortlist means:

> **Offers that the system considers sufficiently relevant to present to the user as opportunities to consider.**

It does not mean:

> guaranteed eligible jobs.

It does not mean:

> jobs for which the candidate will be contacted.

It does not mean:

> jobs the user must apply to.

The user remains the decision-maker.

---

# 17. User Decision and Boundary with Part 2

The final functional action of Part 1 is the user's decision:

```text
Shortlist
    ↓
User reviews offer
    ↓
User decides
    ↓
POSTULER
```

At this exact point, Part 1 ends.

Part 2 begins.

```text
PART 1
Search → Collect → Normalize → Deduplicate → Filter → Match
→ Explain → Recommend → Shortlist
                              ↓
                         USER DECIDES
                           "POSTULER"
                              ↓
PART 2
Application Workflow
```

The application workflow is defined separately in `application-workflow.md`.

---

# 18. End-to-End Functional Flow

```text
                         USER
                           │
                           ▼
                  ┌────────────────┐
                  │ User Profile   │
                  └───────┬────────┘
                          │
                          │
                  ┌───────▼────────┐
                  │ Search          │
                  │ Preferences     │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ SearchCriteria │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Search &       │
                  │ Discovery      │
                  └───────┬────────┘
                          │
                          ▼
                      RawOffers
                          │
                          ▼
                    Normalization
                          │
                          ▼
                      JobOffers
                          │
                          ▼
                   Deduplication
                          │
                          ▼
                       Filtering
                          │
                          ▼
                      Matching
                          │
                          ▼
                     Explanation
                          │
                          ▼
                    Recommendation
                          │
                          ▼
                      SHORTLIST
                          │
                          ▼
                    User decision
                          │
                    ┌─────┴─────┐
                    │ POSTULER  │
                    └─────┬─────┘
                          │
                          ▼
                 Part 2 — Application
```

---

# 19. Functional Responsibility Matrix

| Module | Main question | Main input | Main output |
|---|---|---|---|
| User & Profile | Who is the candidate? | User information | `UserProfile` |
| Search Preferences | What does the user want? | User intent | `SearchPreferences` |
| Search Criteria | How can that intent be searched? | Preferences | `SearchCriteria` |
| Search & Discovery | Where are relevant offers? | Search criteria + source capabilities | `RawOffer[]` |
| Normalization | How do we represent different sources consistently? | `RawOffer` | `JobOffer` |
| Deduplication | Is this the same opportunity? | `JobOffer[]` | Unique `JobOffer[]` |
| Filtering | Does it satisfy the search? | `SearchCriteria` + `JobOffer` | Filter result |
| Matching | How well does the profile fit? | `UserProfile` + `JobOffer` | `MatchingResult` |
| Explanation | Why this result? | Processing results | Explanation |
| Recommendation | Should it be presented? | Filter + Match results | Recommendation |
| Shortlist | Which offers are presented? | Recommendations | Shortlist |
| User Decision | Does the user want to apply? | Shortlist | `POSTULER` |

---

# 20. MVP Scope

The proof of concept prioritizes:

```text
✓ User profile
✓ Search preferences
✓ Source-independent search criteria
✓ Multi-source discovery
✓ Source-specific connectors
✓ Raw offer preservation
✓ Normalization
✓ Deduplication
✓ Filtering
✓ Explainable matching
✓ Recommendation
✓ Shortlist
✓ User decision to apply
```

The MVP does not attempt to fully implement:

```text
✗ Hiring probability prediction
✗ Recruiter behavior prediction
✗ Complete HR assessment
✗ Guaranteed eligibility
✗ Deep evidence-based candidate-job fit
✗ Automatic application as part of Part 1
```

---

# 21. Architectural Principles

### Principle 1 — Discovery and evaluation are different

```text
Discovery
→ Find offers

Evaluation
→ Assess offers
```

### Principle 2 — Filtering and matching are different

```text
Filtering
→ Offer ↔ Search intent

Matching
→ Candidate profile ↔ Offer
```

### Principle 3 — Matching and recommendation are different

```text
Matching
→ Measure correspondence

Recommendation
→ Decide whether to present the opportunity
```

### Principle 4 — Explanation is not another scoring engine

It explains the available assessment and its limitations.

### Principle 5 — Unknown information must remain unknown

The system must not convert missing data into false negative conclusions.

### Principle 6 — The user remains in control

Part 1 ends with:

```text
USER DECIDES
      ↓
POSTULER
```

The agent does not silently turn a recommendation into an application.

### Principle 7 — Part 1 is source-independent after normalization

Once an offer becomes `JobOffer`, downstream processing must not depend on whether it came from Himalayas, RemoteOK, Lever or another source.

---

# 22. Relationship with Part 2

Part 1 and Part 2 form one product, but they have different responsibilities.

```text
┌──────────────────────────────────────┐
│ PART 1 — DISCOVERY & SUGGESTION      │
│                                      │
│ Find → Process → Evaluate → Suggest  │
└───────────────────┬──────────────────┘
                    │
             USER DECISION
                    │
                 POSTULER
                    │
┌───────────────────▼──────────────────┐
│ PART 2 — APPLICATION WORKFLOW        │
│                                      │
│ Prepare → Verify → Execute → Record  │
└──────────────────────────────────────┘
```

Part 2 remains governed by `application-workflow.md`, whose scope explicitly begins at `POSTULER` and ends when the application is submitted or the final human action is completed.

---

# 23. Final Functional Model

The Job Search Agent can therefore be understood as two connected functional systems:

```text
                         JOB SEARCH AGENT
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
             ▼                                     ▼
       PART 1 — DISCOVERY                    PART 2 — APPLICATION
       & SUGGESTION                          WORKFLOW
             │                                     │
       User Profile                          Application Method
             ↓                                     ↓
     Search Preferences                    Requirements
             ↓                                     ↓
      Search Criteria                       Preparation
             ↓                                     ↓
       Job Discovery                       Verification
             ↓                                     ↓
       Normalization                        Execution
             ↓                                     ↓
      Dedup / Filtering                    Application
             ↓
         Matching
             ↓
        Explanation
             ↓
       Recommendation
             ↓
         Shortlist
             ↓
       USER DECISION
             ↓
         POSTULER ───────────────────────────────→ Part 2
```

**Core product principle:**

> **Part 1 reduces the friction of finding and selecting relevant opportunities. Part 2 reduces the friction of preparing and completing the application. The transition between the two is an explicit user decision: `POSTULER`.**
