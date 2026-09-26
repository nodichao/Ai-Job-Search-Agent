import pytest
from pydantic import ValidationError

from app.core.errors import ShortlistDuplicateError, ShortlistIdentityError, ShortlistPersistenceError
from app.domain.job_offer import JobOffer
from app.domain.shortlist import ShortlistStatus, ShortlistStatusUpdate
from app.repositories.sqlite_shortlist_repository import SQLiteShortlistRepository
from app.services.shortlist_service import ShortlistService


def offer(*, source_id="remote-1", url="https://jobs.example/remote-1", slug="remote-1"):
    return JobOffer.model_validate({
        "identity": {"sourceId": source_id, "offerUrl": url, "slug": slug},
        "source": {"name": "RemoteOK", "url": "https://remoteok.example/", "retrievedAt": "2026-09-26T12:00:00Z"},
        "position": {"title": "Platform Engineer", "sourceSummary": "Source supplied summary"},
        "company": {"name": "ExampleCo"},
        "application": {"applyUrl": "https://apply.example/remote-1"},
    })


def service(path):
    return ShortlistService(SQLiteShortlistRepository(f"sqlite:///{path}"))


def test_add_list_and_get_preserve_canonical_offer_identity_and_source_provenance(tmp_path):
    shortlist = service(tmp_path / "shortlist.db")
    saved = shortlist.add(offer())

    assert saved.status is ShortlistStatus.SAVED
    assert saved.offer.identity.source_id == "remote-1"
    assert saved.offer.source.name == "RemoteOK"
    assert str(saved.offer.source.url) == "https://remoteok.example/"
    assert saved.offer.source.retrieved_at is not None
    assert str(saved.offer.application.apply_url) == "https://apply.example/remote-1"
    assert shortlist.get(saved.id) == saved
    assert shortlist.list() == [saved]


def test_duplicate_source_identity_or_offer_url_is_rejected(tmp_path):
    shortlist = service(tmp_path / "shortlist.db")
    saved = shortlist.add(offer())
    shortlist.update_status(saved.id, ShortlistStatus.INTERESTED)
    with pytest.raises(ShortlistDuplicateError):
        shortlist.add(offer())
    assert shortlist.get(saved.id).status is ShortlistStatus.INTERESTED
    # A stable offer URL also catches a duplicate whose source ID has changed.
    with pytest.raises(ShortlistDuplicateError):
        shortlist.add(offer(source_id="different-source-id", slug="different-slug"))


def test_offer_url_duplicate_key_ignores_fragment_and_query_order(tmp_path):
    shortlist = service(tmp_path / "shortlist.db")
    shortlist.add(offer(source_id="one", url="https://jobs.example/offer?b=2&a=1#first", slug="one"))
    with pytest.raises(ShortlistDuplicateError):
        shortlist.add(offer(source_id="two", url="https://jobs.example/offer?a=1&b=2#second", slug="two"))


def test_all_user_declared_statuses_can_be_set_and_invalid_status_is_rejected(tmp_path):
    shortlist = service(tmp_path / "shortlist.db")
    saved = shortlist.add(offer())
    for status in ShortlistStatus:
        updated = shortlist.update_status(saved.id, status)
        assert updated is not None and updated.status is status
    assert shortlist.get(saved.id).status is ShortlistStatus.ARCHIVED
    with pytest.raises(ValidationError):
        ShortlistStatusUpdate.model_validate({"status": "SUBMITTED"})


def test_missing_entry_and_deletion_results_are_explicit(tmp_path):
    shortlist = service(tmp_path / "shortlist.db")
    assert shortlist.get("missing") is None
    assert shortlist.update_status("missing", ShortlistStatus.APPLIED) is None
    assert shortlist.delete("missing") is False
    saved = shortlist.add(offer())
    assert shortlist.delete(saved.id) is True
    assert shortlist.get(saved.id) is None
    assert shortlist.list() == []


def test_saved_offer_survives_service_and_repository_recreation(tmp_path):
    path = tmp_path / "persistent.db"
    first = service(path)
    saved = first.add(offer())
    second = service(path)
    assert second.get(saved.id) == saved


def test_title_alone_is_not_a_stable_deduplication_identity(tmp_path):
    shortlist = service(tmp_path / "shortlist.db")
    unstable = offer(source_id=None, url=None, slug=None)
    with pytest.raises(ShortlistIdentityError):
        shortlist.add(unstable)


def test_database_failures_are_wrapped_without_exposing_path(tmp_path):
    directory = tmp_path / "not-a-db-file"
    directory.mkdir()
    shortlist = service(directory)
    with pytest.raises(ShortlistPersistenceError, match="storage is unavailable") as error:
        shortlist.list()
    assert str(tmp_path) not in str(error.value)
