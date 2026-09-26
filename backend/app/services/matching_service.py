"""Deterministic, evidence-based profile-to-offer matching."""
from app.domain.job_offer import JobOffer, RemoteScope
from app.domain.matching import EvidenceStatus, MatchDimension, MatchingResult
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.services.salary_comparison import salary_status
from app.services.text_matching import normalize_term, token_jaccard


class MatchingService:
    # Centralized implementation weights required by the MVP specification.
    WEIGHTS = {"skills": 0.50, "preferences": 0.25, "experience": 0.15, "roleAlignment": 0.10}

    def match(
        self,
        profile: UserProfile,
        preferences: SearchPreferences,
        offer: JobOffer,
    ) -> MatchingResult:
        dimensions = [
            self._skills(profile, offer),
            self._preferences(preferences, offer),
            self._experience(profile, offer),
            self._role(profile, offer),
        ]
        evaluated = [dimension for dimension in dimensions if dimension.score is not None]
        total_weight = sum(self.WEIGHTS[dimension.name] for dimension in evaluated)
        if total_weight:
            for dimension in evaluated:
                dimension.weight = self.WEIGHTS[dimension.name] / total_weight
            score = sum(d.score * d.weight for d in evaluated if d.score is not None)
            confidence = total_weight
        else:
            score, confidence = None, 0.0

        matched = [item for dimension in dimensions for item in dimension.matched_criteria]
        missing = [item for dimension in dimensions for item in dimension.missing_criteria]
        conflicts = [item for dimension in dimensions for item in dimension.conflicts]
        return MatchingResult(
            score=round(score, 2) if score is not None else None,
            confidence=round(confidence, 4),
            dimensions=dimensions,
            matched_criteria=matched,
            missing_criteria=missing,
            conflicts=conflicts,
        )

    def _skills(self, profile: UserProfile, offer: JobOffer) -> MatchDimension:
        if not profile.skills or not offer.position.skills:
            reason = "Candidate skills or offer skills are unavailable"
            return MatchDimension(name="skills", status=EvidenceStatus.UNKNOWN, evidence=[reason],
                                 missingCriteria=[f"skills: {reason}"])
        candidate = {normalize_term(value) for value in profile.skills if normalize_term(value)}
        requested = {normalize_term(value) for value in offer.position.skills if normalize_term(value)}
        if not requested or not candidate:
            return MatchDimension(name="skills", status=EvidenceStatus.UNKNOWN, evidence=["No comparable skill terms"],
                                 missingCriteria=["skills: no comparable terms"])
        overlap = candidate & requested
        score = 100 * len(overlap) / len(requested)
        missing = sorted(requested - candidate)
        status = EvidenceStatus.SATISFIED if not missing else EvidenceStatus.UNKNOWN
        evidence = [f"Matched skills: {', '.join(sorted(overlap))}"] if overlap else []
        if missing:
            evidence.append(f"Not evidenced in profile: {', '.join(missing)}")
        matched_items = [f"skills: {', '.join(sorted(overlap))}"] if overlap else []
        missing_items = [f"skills: Not evidenced in profile: {', '.join(missing)}"] if missing else []
        return MatchDimension(name="skills", status=status, score=score, evidence=evidence,
                              matchedCriteria=matched_items, missingCriteria=missing_items)

    def _experience(self, profile: UserProfile, offer: JobOffer) -> MatchDimension:
        years, minimum = profile.total_experience_years, offer.experience.minimum_years
        if years is None or minimum is None:
            return MatchDimension(name="experience", status=EvidenceStatus.UNKNOWN,
                                 evidence=["Candidate years or offer minimum experience are unavailable"],
                                 missingCriteria=["experience: candidate years or offer minimum are unavailable"])
        if minimum <= 0:
            return MatchDimension(name="experience", status=EvidenceStatus.SATISFIED, score=100,
                                 evidence=["No positive minimum experience is stated"],
                                 matchedCriteria=["experience: no positive minimum is stated"])
        score = min(100.0, 100 * years / minimum)
        if years >= minimum:
            return MatchDimension(name="experience", status=EvidenceStatus.SATISFIED, score=100,
                                 evidence=[f"Candidate: {years:g} years; offer minimum: {minimum:g} years"],
                                 matchedCriteria=[f"experience: {years:g} years meets minimum {minimum:g} years"])
        return MatchDimension(name="experience", status=EvidenceStatus.CONFLICT, score=score,
                             evidence=[f"Candidate: {years:g} years; offer minimum: {minimum:g} years"],
                             conflicts=[f"experience: {years:g} years is below minimum {minimum:g} years"])

    def _role(self, profile: UserProfile, offer: JobOffer) -> MatchDimension:
        if not profile.job_titles or not offer.position.title.strip():
            return MatchDimension(name="roleAlignment", status=EvidenceStatus.UNKNOWN,
                                 evidence=["Candidate titles or offer title are unavailable"],
                                 missingCriteria=["roleAlignment: candidate titles or offer title are unavailable"])
        similarities = [(title, token_jaccard(title, offer.position.title)) for title in profile.job_titles]
        title, score_ratio = max(similarities, key=lambda pair: pair[1])
        score = score_ratio * 100
        if score_ratio == 0:
            return MatchDimension(name="roleAlignment", status=EvidenceStatus.UNKNOWN, score=0,
                                 evidence=["No shared title terms; semantic alignment was not inferred"],
                                 missingCriteria=["roleAlignment: no shared title terms; semantic alignment was not inferred"])
        return MatchDimension(name="roleAlignment", status=EvidenceStatus.SATISFIED, score=score,
                             evidence=[f"Title term overlap: {title} / {offer.position.title}"],
                             matchedCriteria=[f"roleAlignment: title term overlap for {title} / {offer.position.title}"])

    def _preferences(self, preferences: SearchPreferences, offer: JobOffer) -> MatchDimension:
        checks: list[tuple[str, EvidenceStatus | None, str | None]] = []

        if preferences.remote is not None:
            actual_remote = offer.location.remote
            if actual_remote is None and offer.location.remote_scope not in {RemoteScope.UNKNOWN, RemoteScope.HYBRID}:
                actual_remote = True
            matches = actual_remote is preferences.remote
            checks.append(("remote", EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT if actual_remote is not None else None,
                           "Offer remote status matches preference" if matches else "Offer remote status conflicts with preference" if actual_remote is not None else None))

        if preferences.locations:
            actual = [*offer.location.locations, *offer.location.cities]
            if not actual and offer.company.location:
                actual = [offer.company.location]
            known = bool(actual)
            matched = any(normalize_term(w) == normalize_term(a) or normalize_term(w) in normalize_term(a)
                          or normalize_term(a) in normalize_term(w) for w in preferences.locations for a in actual)
            checks.append(("locations", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           "Offer location matches preferences" if matched else "Offer location differs from preferences" if known else None))
        if preferences.countries:
            actual = offer.location.countries
            known = bool(actual)
            matched = bool({normalize_term(w) for w in preferences.countries} & {normalize_term(a) for a in actual})
            checks.append(("countries", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           "Offer country matches preferences" if matched else "Offer country differs from preferences" if known else None))
        if preferences.seniority:
            actual = offer.employment.seniority.value
            known = actual != "UNKNOWN"
            matched = known and any(normalize_term(actual) == normalize_term(w) for w in preferences.seniority)
            checks.append(("seniority", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           f"Offer seniority: {actual}" if known else None))
        if preferences.employment_types:
            actual = offer.employment.type.value
            known = actual != "UNKNOWN"
            matched = known and any(normalize_term(actual) == normalize_term(w) for w in preferences.employment_types)
            checks.append(("employmentTypes", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           f"Offer employment type: {actual}" if known else None))
        if preferences.skills:
            actual = {normalize_term(value) for value in offer.position.skills}
            known = bool(actual)
            matched = bool(actual & {normalize_term(value) for value in preferences.skills})
            checks.append(("skillsPreference", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           "At least one preferred skill is listed" if matched else "No preferred skill is listed" if known else None))
        if preferences.companies:
            actual = offer.company.name
            known = bool(actual)
            matched = bool(actual) and any(normalize_term(actual) == normalize_term(w) for w in preferences.companies)
            checks.append(("companies", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           "Offer company matches preference" if matched else "Offer company differs from preference" if known else None))
        if preferences.timezone:
            actual = offer.location.timezone_restrictions
            known = bool(actual)
            matched = any(normalize_term(preferences.timezone) == normalize_term(value) for value in actual)
            checks.append(("timezone", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if known else None,
                           "Timezone restriction matches preference" if matched else "Timezone restrictions differ" if known else None))
        if preferences.salary:
            status, evidence = salary_status(preferences.salary, offer)
            checks.append(("salary", status if status is not EvidenceStatus.UNKNOWN else None, evidence))
        if preferences.job_titles:
            matched = any(token_jaccard(title, offer.position.title) > 0 for title in preferences.job_titles)
            checks.append(("jobTitles", EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT,
                           "Offer title shares terms with a preferred title" if matched else "No shared title terms"))

        known = [status for _, status, _ in checks if status is not None]
        if not known:
            return MatchDimension(name="preferences", status=EvidenceStatus.UNKNOWN,
                                 evidence=[f"{name}: evidence unavailable" for name, _, _ in checks] or ["No search preferences supplied"],
                                 missingCriteria=[f"preferences: {name} evidence unavailable" for name, _, _ in checks] or ["preferences: no search preferences supplied"])
        score = 100 * sum(status is EvidenceStatus.SATISFIED for status in known) / len(known)
        unknown = [(name, text) for name, item, text in checks if item is None]
        status = (EvidenceStatus.CONFLICT if any(item is EvidenceStatus.CONFLICT for item in known)
                  else EvidenceStatus.UNKNOWN if unknown else EvidenceStatus.SATISFIED)
        evidence = [text for _, _, text in checks if text]
        evidence.extend(f"{name}: evidence unavailable" for name, item, _ in checks if item is None)
        matched_items = [f"preferences: {name} satisfied" for name, item, _ in checks if item is EvidenceStatus.SATISFIED]
        missing_items = [f"preferences: {name} evidence unavailable" for name, item, _ in checks if item is None]
        conflict_items = [f"preferences: {name} conflicts with supplied offer evidence" for name, item, _ in checks if item is EvidenceStatus.CONFLICT]
        return MatchDimension(name="preferences", status=status, score=score, evidence=evidence,
                              matchedCriteria=matched_items, missingCriteria=missing_items, conflicts=conflict_items)
