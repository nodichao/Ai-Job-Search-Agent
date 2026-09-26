"""Build user-facing match explanations from structured evidence only."""
from app.domain.matching import FilteringResult, MatchExplanation, MatchingResult


class ExplanationService:
    def explain(self, filtering: FilteringResult, matching: MatchingResult) -> MatchExplanation:
        reasons: list[str] = []
        if filtering.included:
            reasons.append("Offer retained by filtering; no known REQUIRED criterion conflict.")
        else:
            reasons.append("Offer excluded by at least one known REQUIRED criterion conflict.")
        reasons.extend(f"Satisfied search criterion: {name}" for name in filtering.satisfied_criteria)
        reasons.extend(f"Search criterion unknown: {name}" for name in filtering.unknown_criteria)
        reasons.extend(f"Conflicting search criterion: {name}" for name in filtering.conflicts)
        reasons.extend(f"{item.name}: {evidence}" for item in matching.dimensions for evidence in item.evidence)
        if matching.score is None:
            reasons.append("No matching dimension had enough evidence to calculate a score.")
        else:
            reasons.append("Score is a deterministic relevance measure, not a hiring probability.")
        return MatchExplanation(
            score=matching.score,
            confidence=matching.confidence,
            dimensions=matching.dimensions,
            satisfied_criteria=filtering.satisfied_criteria + matching.matched_criteria,
            unknown_criteria=filtering.unknown_criteria + matching.missing_criteria,
            conflicts=filtering.conflicts + matching.conflicts,
            reasons=reasons,
        )
