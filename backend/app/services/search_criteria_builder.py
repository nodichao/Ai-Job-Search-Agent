"""Translate submitted search preferences into source-independent criteria."""
from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import SearchPreferences


def criteria_from_preferences(preferences: SearchPreferences) -> SearchCriteria:
    """Copy comparable fields; leave source-specific/unsupported criteria empty."""
    return SearchCriteria(
        jobTitles=preferences.job_titles,
        locations=preferences.locations,
        countries=preferences.countries,
        remote=preferences.remote,
        seniority=preferences.seniority,
        employmentTypes=preferences.employment_types,
        skills=preferences.skills,
        salary=preferences.salary,
        companies=preferences.companies,
        timezone=preferences.timezone,
    )
