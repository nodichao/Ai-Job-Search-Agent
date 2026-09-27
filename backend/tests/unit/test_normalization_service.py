from app.connectors.base import RawOffer
from app.services.normalization_service import NormalizationService


def test_normalization_status_counts_rejections_per_source_and_keeps_valid_offers():
    valid = RawOffer(
        source_name="RemoteOK",
        source_id="good",
        payload={"id": "good", "position": "Backend Developer"},
    )
    invalid_one = RawOffer(source_name="RemoteOK", source_id="bad-1", payload={"id": "bad-1"})
    invalid_two = RawOffer(source_name="RemoteOK", source_id="bad-2", payload={"id": "bad-2", "position": " "})

    result = NormalizationService().normalize_with_status([valid, invalid_one, invalid_two])

    assert [offer.identity.source_id for offer in result.offers] == ["good"]
    assert result.total_rejected == 2
    assert result.rejected_by_source == {"RemoteOK": 2}
    # Existing callers of normalize() continue to receive just the successful offers.
    assert [offer.identity.source_id for offer in NormalizationService().normalize([valid])] == ["good"]


def test_missing_normalizer_is_counted_as_a_source_rejection():
    raw = RawOffer(source_name="FutureSource", source_id="1", payload={"id": "1"})
    result = NormalizationService().normalize_with_status([raw])
    assert result.offers == []
    assert result.total_rejected == 1
    assert result.rejected_by_source == {"FutureSource": 1}
