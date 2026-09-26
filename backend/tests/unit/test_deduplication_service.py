from copy import deepcopy

from app.domain.job_offer import JobOffer, OfferIdentity, OfferLocation, OfferSource, Position
from app.services.deduplication_service import DeduplicationService


def offer(*, source="RemoteOK", source_id=None, url=None, company="Acme", title="Engineer", locations=None):
    return JobOffer(
        identity=OfferIdentity(sourceId=source_id, offerUrl=url),
        source=OfferSource(name=source),
        position=Position(title=title),
        company={"name": company},
        location=OfferLocation(locations=locations or []),
    )


def test_exact_source_identity_keeps_first_without_mutating_input():
    first = offer(source_id="42", title="Engineer")
    duplicate = offer(source=" remoteok ", source_id=" 42 ", title="Different")
    before = deepcopy(first.model_dump())

    result = DeduplicationService().deduplicate([first, duplicate])

    assert result == [first]
    assert first.model_dump() == before


def test_offer_url_normalization_preserves_query_components():
    first = offer(source="A", url="https://EXAMPLE.com:443/jobs/42/")
    same = offer(source="B", url="https://example.com/jobs/42")
    different_query = offer(source="C", url="https://example.com/jobs/42?team=1")

    assert DeduplicationService().deduplicate([first, same, different_query]) == [first, different_query]


def test_cross_source_requires_exact_company_title_and_overlapping_location():
    first = offer(source="A", company="Acme", title="Engineer", locations=["Dakar, Senegal"])
    same = offer(source="B", company=" ACME ", title=" engineer ", locations=["Dakar, Senegal"])
    other_title = offer(source="C", company="Acme", title="Senior Engineer", locations=["Dakar, Senegal"])
    other_location = offer(source="D", company="Acme", title="Engineer", locations=["Paris, France"])
    unknown_location = offer(source="E", company="Acme", title="Engineer")

    assert DeduplicationService().deduplicate([first, same, other_title, other_location, unknown_location]) == [
        first, other_title, other_location, unknown_location
    ]


def test_cross_source_requires_distinct_sources_and_allows_missing_identity():
    first = offer(source="A", company="Acme", title="Engineer", locations=["Remote - EU"])
    same_source = offer(source="A", company="Acme", title="Engineer", locations=["Remote - EU"])
    no_company = offer(source="B", company=None, title="Engineer", locations=["Remote - EU"])
    no_title = offer(source="C", company="Acme", title=" ", locations=["Remote - EU"])

    assert DeduplicationService().deduplicate([first, same_source, no_company, no_title]) == [
        first, same_source, no_company, no_title
    ]


def test_empty_input_and_iterable_are_supported():
    first = offer(source_id="1")
    assert DeduplicationService().deduplicate(iter([first])) == [first]
    assert DeduplicationService().deduplicate([]) == []
