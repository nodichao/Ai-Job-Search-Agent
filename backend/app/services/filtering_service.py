"""Evaluate explicit search criteria independently from candidate matching."""
from collections.abc import Mapping, Sequence

from app.domain.job_offer import JobOffer, RemoteScope
from app.domain.matching import CriterionAssessment, EvidenceStatus, FilteringResult
from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import PreferenceStrength
from app.services.salary_comparison import salary_status
from app.services.text_matching import normalize_term, terms_overlap


class FilteringService:
    """Post-retrieval filter; only known REQUIRED conflicts exclude an offer."""

    def evaluate(
        self,
        criteria: SearchCriteria,
        offer: JobOffer,
        strengths: Mapping[str, PreferenceStrength | str] | None = None,
    ) -> FilteringResult:
        strengths = strengths or {}
        assessments: list[CriterionAssessment] = []

        def add(name: str, has_value: bool, status: EvidenceStatus | None, evidence: str | None) -> None:
            if not has_value:
                return
            strength = _strength_for(strengths, name)
            assessments.append(CriterionAssessment(
                name=name,
                strength=strength,
                status=status or EvidenceStatus.UNKNOWN,
                evidence=[evidence] if evidence else [],
            ))

        if criteria.job_titles:
            matched = [wanted for wanted in criteria.job_titles if terms_overlap(wanted, offer.position.title)]
            add("jobTitles", True, EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT,
                f"Offer title: {offer.position.title}; requested: {', '.join(criteria.job_titles)}")

        if criteria.keywords:
            searchable = " ".join([
                offer.position.title, offer.position.source_summary or "", offer.position.description or "",
                *offer.position.skills, *offer.position.categories,
            ])
            matched = [term for term in criteria.keywords if normalize_term(term) and normalize_term(term) in normalize_term(searchable)]
            add("keywords", True, EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT if searchable.strip() else EvidenceStatus.UNKNOWN,
                f"Keyword evidence found: {', '.join(matched)}" if matched else "Offer text is available but contains none of the requested keywords" if searchable.strip() else None)

        if criteria.locations:
            actual = [*offer.location.locations, *offer.location.cities]
            if actual:
                matches = [wanted for wanted in criteria.locations for found in actual if terms_overlap(wanted, found)]
                add("locations", True, EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT,
                    f"Offer locations: {', '.join(actual)}")
            elif offer.company.location:
                matches = [wanted for wanted in criteria.locations if terms_overlap(wanted, offer.company.location)]
                add("locations", True, EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT,
                    f"Company location: {offer.company.location}")
            else:
                add("locations", True, EvidenceStatus.UNKNOWN, None)

        if criteria.countries:
            actual = offer.location.countries
            if actual:
                matches = {normalize_term(item) for item in criteria.countries} & {normalize_term(item) for item in actual}
                add("countries", True, EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT,
                    f"Offer countries: {', '.join(actual)}")
            else:
                add("countries", True, EvidenceStatus.UNKNOWN, None)

        if criteria.remote is not None:
            remote = offer.location.remote
            if remote is None and offer.location.remote_scope not in {RemoteScope.UNKNOWN, RemoteScope.HYBRID}:
                remote = True
            add("remote", True,
                EvidenceStatus.UNKNOWN if remote is None else EvidenceStatus.SATISFIED if remote == criteria.remote else EvidenceStatus.CONFLICT,
                None if remote is None else f"Offer remote value: {str(remote).lower()}")

        if criteria.seniority:
            actual = offer.employment.seniority.value
            known = actual != "UNKNOWN"
            matches = any(normalize_term(actual) == normalize_term(value) for value in criteria.seniority)
            add("seniority", True,
                EvidenceStatus.SATISFIED if known and matches else EvidenceStatus.CONFLICT if known else EvidenceStatus.UNKNOWN,
                f"Offer seniority: {actual}" if known else None)

        if criteria.employment_types:
            actual = offer.employment.type.value
            known = actual != "UNKNOWN"
            matches = any(normalize_term(actual) == normalize_term(value) for value in criteria.employment_types)
            add("employmentTypes", True,
                EvidenceStatus.SATISFIED if known and matches else EvidenceStatus.CONFLICT if known else EvidenceStatus.UNKNOWN,
                f"Offer employment type: {actual}" if known else None)

        if criteria.skills:
            actual = offer.position.skills
            if actual:
                matches = [wanted for wanted in criteria.skills if any(normalize_term(wanted) == normalize_term(found) for found in actual)]
                add("skills", True, EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT,
                    f"Offer skills: {', '.join(actual)}")
            else:
                add("skills", True, EvidenceStatus.UNKNOWN, None)

        if criteria.companies:
            actual = offer.company.name
            if actual:
                matches = any(terms_overlap(wanted, actual) for wanted in criteria.companies)
                add("companies", True, EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT,
                    f"Offer company: {actual}")
            else:
                add("companies", True, EvidenceStatus.UNKNOWN, None)

        if criteria.timezone:
            actual = offer.location.timezone_restrictions
            if actual:
                matches = any(normalize_term(criteria.timezone) == normalize_term(item) for item in actual)
                add("timezone", True, EvidenceStatus.SATISFIED if matches else EvidenceStatus.CONFLICT,
                    f"Offer timezone restrictions: {', '.join(actual)}")
            else:
                add("timezone", True, EvidenceStatus.UNKNOWN, None)

        if criteria.departments:
            actual = offer.employment.department
            if actual:
                matched = any(terms_overlap(wanted, actual) for wanted in criteria.departments)
                add("departments", True, EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT,
                    f"Offer department: {actual}")
            else:
                add("departments", True, EvidenceStatus.UNKNOWN, None)

        if criteria.teams:
            actual = offer.employment.team
            if actual:
                matched = any(terms_overlap(wanted, actual) for wanted in criteria.teams)
                add("teams", True, EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT,
                    f"Offer team: {actual}")
            else:
                add("teams", True, EvidenceStatus.UNKNOWN, None)

        if criteria.tags:
            actual = offer.position.categories
            if actual:
                matched = any(normalize_term(wanted) == normalize_term(found)
                              for wanted in criteria.tags for found in actual)
                add("tags", True, EvidenceStatus.SATISFIED if matched else EvidenceStatus.CONFLICT,
                    f"Offer categories: {', '.join(actual)}")
            else:
                add("tags", True, EvidenceStatus.UNKNOWN, None)

        if criteria.salary is not None:
            status, evidence = salary_status(criteria.salary, offer)
            add("salary", True, status, evidence)

        conflicts = [item.name for item in assessments if item.status is EvidenceStatus.CONFLICT]
        satisfied = [item.name for item in assessments if item.status is EvidenceStatus.SATISFIED]
        unknown = [item.name for item in assessments if item.status is EvidenceStatus.UNKNOWN]
        excluded = any(item.strength is PreferenceStrength.REQUIRED and item.status is EvidenceStatus.CONFLICT for item in assessments)
        return FilteringResult(
            included=not excluded,
            criteria=assessments,
            satisfied_criteria=satisfied,
            unknown_criteria=unknown,
            conflicts=conflicts,
        )

    def filter(
        self,
        criteria: SearchCriteria,
        offers: Sequence[JobOffer],
        strengths: Mapping[str, PreferenceStrength | str] | None = None,
    ) -> list[tuple[JobOffer, FilteringResult]]:
        """Return per-offer decisions, retaining rejected offers for explanation."""
        return [(offer, self.evaluate(criteria, offer, strengths)) for offer in offers]


def _strength_for(strengths: Mapping[str, PreferenceStrength | str], name: str) -> PreferenceStrength:
    aliases = {name, name[0].lower() + name[1:]}
    snake = "".join(("_" + c.lower()) if c.isupper() else c for c in name).lstrip("_")
    aliases.add(snake)
    for alias in aliases:
        if alias in strengths:
            try:
                return PreferenceStrength(strengths[alias])
            except ValueError:
                break
    return PreferenceStrength.PREFERRED
