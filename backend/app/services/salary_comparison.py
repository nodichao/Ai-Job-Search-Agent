"""Conservative comparison of structured salary ranges with known units."""
from app.domain.job_offer import JobOffer
from app.domain.matching import EvidenceStatus
from app.domain.search_preferences import SalaryPreference
from app.services.text_matching import normalize_term


def salary_status(preference: SalaryPreference, offer: JobOffer) -> tuple[EvidenceStatus, str | None]:
    # Without both units, numeric ranges cannot be compared safely.
    if not preference.currency or not preference.period:
        return EvidenceStatus.UNKNOWN, None
    comparable = [
        component
        for component in (offer.compensation.components if offer.compensation else [])
        if component.currency
        and component.period
        and normalize_term(component.currency) == normalize_term(preference.currency)
        and normalize_term(component.period) == normalize_term(preference.period)
    ]
    if not comparable:
        return EvidenceStatus.UNKNOWN, None
    conflicts = []
    for component in comparable:
        low = component.min if component.min is not None else component.amount
        high = component.max if component.max is not None else component.amount
        if low is None and high is None:
            continue
        below = preference.minimum is not None and high is not None and high < preference.minimum
        above = preference.maximum is not None and low is not None and low > preference.maximum
        if not below and not above:
            return EvidenceStatus.SATISFIED, f"Offer compensation in {preference.currency}/{preference.period} overlaps requested range"
        conflicts.append(f"{low}–{high} {preference.currency}/{preference.period}")
    if not conflicts:
        return EvidenceStatus.UNKNOWN, None
    return EvidenceStatus.CONFLICT, f"Offer compensation: {', '.join(conflicts)}"
