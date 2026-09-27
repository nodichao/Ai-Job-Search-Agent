"""Apply source normalizers after collection, keeping RawOffer out of the API."""
import logging
from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Protocol

from app.connectors.base import RawOffer
from app.connectors.lever import LeverNormalizer
from app.connectors.himalayas import HimalayasNormalizer
from app.connectors.remoteok import RemoteOKNormalizer
from app.core.errors import NormalizationError
from app.domain.job_offer import JobOffer

logger = logging.getLogger(__name__)


class OfferNormalizer(Protocol):
    def normalize(self, raw_offer: RawOffer) -> JobOffer: ...


@dataclass(frozen=True)
class NormalizationResult:
    offers: list[JobOffer]
    rejected_by_source: dict[str, int] = field(default_factory=dict)

    @property
    def total_rejected(self) -> int:
        return sum(self.rejected_by_source.values())


class NormalizationService:
    def __init__(self, normalizers: Mapping[str, OfferNormalizer] | None = None) -> None:
        self._normalizers = dict(normalizers if normalizers is not None else {
            "RemoteOK": RemoteOKNormalizer(),
            "Lever": LeverNormalizer(),
            "Himalayas": HimalayasNormalizer(),
        })

    def normalize(self, raw_offers: list[RawOffer]) -> list[JobOffer]:
        """Backward-compatible helper returning only successfully normalized offers."""
        return self.normalize_with_status(raw_offers).offers

    def normalize_with_status(self, raw_offers: list[RawOffer]) -> NormalizationResult:
        offers: list[JobOffer] = []
        rejected_by_source: dict[str, int] = {}
        for raw_offer in raw_offers:
            normalizer = self._normalizers.get(raw_offer.source_name)
            if normalizer is None:
                rejected_by_source[raw_offer.source_name] = rejected_by_source.get(raw_offer.source_name, 0) + 1
                logger.warning(
                    "No normalizer is configured for job source; source=%s",
                    raw_offer.source_name,
                )
                continue
            try:
                offers.append(normalizer.normalize(raw_offer))
            except NormalizationError as exc:
                rejected_by_source[raw_offer.source_name] = rejected_by_source.get(raw_offer.source_name, 0) + 1
                logger.warning(
                    "Job offer normalization failed; source=%s error_type=%s",
                    raw_offer.source_name,
                    type(exc).__name__,
                )
        return NormalizationResult(offers=offers, rejected_by_source=rejected_by_source)
