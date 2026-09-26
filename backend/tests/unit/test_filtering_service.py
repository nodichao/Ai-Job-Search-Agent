from app.domain.job_offer import JobOffer
from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import PreferenceStrength
from app.services.filtering_service import FilteringService


def offer(**updates):
    data = {
        "identity": {"sourceId": "1", "offerUrl": "https://jobs.example/1"},
        "source": {"name": "Fixture"},
        "position": {"title": "Platform Engineer", "skills": ["Python"]},
        "location": {"remote": True, "countries": ["SN"], "locations": ["Dakar"]},
        "employment": {"type": "FULL_TIME", "seniority": "SENIOR", "department": "Engineering", "team": "Platform"},
        "company": {"name": "ExampleCo"},
    }
    for key, value in updates.items():
        data[key] = value
    return JobOffer.model_validate(data)


def test_required_criteria_satisfied_or_known_conflicts_exclude():
    service = FilteringService()
    criteria = SearchCriteria(remote=True, countries=["SN"], employmentTypes=["FULL_TIME"])
    strengths = {"remote": "REQUIRED", "countries": "REQUIRED", "employmentTypes": "REQUIRED"}
    result = service.evaluate(criteria, offer(), strengths)
    assert result.included
    assert set(result.satisfied_criteria) == {"remote", "countries", "employmentTypes"}

    rejected = service.evaluate(criteria, offer(location={"remote": False, "countries": ["US"]}), strengths)
    assert not rejected.included
    assert set(rejected.conflicts) == {"remote", "countries"}


def test_unknown_required_evidence_does_not_exclude_and_is_not_conflict():
    result = FilteringService().evaluate(
        SearchCriteria(remote=True, countries=["SN"]),
        offer(location={"remote": None, "countries": []}),
        {"remote": PreferenceStrength.REQUIRED, "countries": PreferenceStrength.REQUIRED},
    )
    assert result.included
    assert set(result.unknown_criteria) == {"remote", "countries"}
    assert result.conflicts == []

    hybrid = FilteringService().evaluate(
        SearchCriteria(remote=True), offer(location={"remote": None, "remoteScope": "HYBRID"}),
        {"remote": "REQUIRED"},
    )
    assert hybrid.included and hybrid.unknown_criteria == ["remote"]


def test_preferred_optional_and_informational_conflicts_do_not_exclude():
    criteria = SearchCriteria(jobTitles=["Designer"], companies=["Other"])
    strengths = {"jobTitles": "PREFERRED", "companies": "INFORMATIONAL"}
    result = FilteringService().evaluate(criteria, offer(), strengths)
    assert result.included
    assert set(result.conflicts) == {"jobTitles", "companies"}
    assert FilteringService().evaluate(
        SearchCriteria(jobTitles=["Designer"]), offer(), {"jobTitles": "OPTIONAL"}
    ).included


def test_criteria_without_evidence_are_unknown_and_empty_criteria_are_neutral():
    result = FilteringService().evaluate(
        SearchCriteria(skills=["Go"], locations=["Dakar"], salary={"minimum": 1000}),
        offer(position={"title": "Engineer"}, location={}, company={}),
        {"skills": "REQUIRED", "locations": "REQUIRED", "salary": "REQUIRED"},
    )
    assert result.included
    assert set(result.unknown_criteria) == {"skills", "locations", "salary"}
    empty = FilteringService().filter(SearchCriteria(), [offer(), offer(identity={"sourceId": "2"})])
    assert len(empty) == 2 and all(decision.included for _, decision in empty)


def test_filter_preserves_each_offer_and_distinguishes_outcomes():
    offers = [offer(), offer(position={"title": "Designer"})]
    results = FilteringService().filter(
        SearchCriteria(jobTitles=["Platform Engineer"]), offers, {"jobTitles": "REQUIRED"}
    )
    assert [item.included for _, item in results] == [True, False]
    assert [item.position.title for item, _ in results] == ["Platform Engineer", "Designer"]
