from app.domain.search_preferences import SearchPreferences
from app.services.search_criteria_builder import criteria_from_preferences


def test_preferences_are_copied_to_source_independent_criteria_only():
    criteria = criteria_from_preferences(SearchPreferences(
        jobTitles=["Platform Engineer"],
        locations=["Dakar"],
        countries=["SN"],
        remote=False,
        seniority=["SENIOR"],
        employmentTypes=["FULL_TIME"],
        skills=["Python"],
        companies=["Example"],
        timezone="GMT",
    ))
    assert criteria.job_titles == ["Platform Engineer"]
    assert criteria.locations == ["Dakar"]
    assert criteria.countries == ["SN"]
    assert criteria.remote is False
    assert criteria.seniority == ["SENIOR"]
    assert criteria.employment_types == ["FULL_TIME"]
    assert criteria.skills == ["Python"]
    assert criteria.companies == ["Example"]
    assert criteria.timezone == "GMT"
    assert criteria.keywords == []
    assert criteria.tags == []
