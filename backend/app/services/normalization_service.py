"""Apply source normalizers after collection, keeping RawOffer out of the API."""
import logging
from collections.abc import Mapping
from typing import Protocol

from app.connectors.base import RawOffer
from app.connectors.lever import LeverNormalizer
from app.connectors.remoteok import RemoteOKNormalizer
from app.core.errors import NormalizationError
from app.domain.job_offer import JobOffer

logger = logging.getLogger(__name__)


class OfferNormalizer(Protocol):
    def normalize(self, raw_offer: RawOffer) -> JobOffer: ...


class NormalizationService:
    def __init__(self, normalizers: Mapping[str, OfferNormalizer] | None = None) -> None:
        self._normalizers = dict(normalizers if normalizers is not None else {
            "RemoteOK": RemoteOKNormalizer(),
            "Lever": LeverNormalizer(),
        })

    def normalize(self, raw_offers: list[RawOffer]) -> list[JobOffer]:
        offers: list[JobOffer] = []
        for raw_offer in raw_offers:
            normalizer = self._normalizers.get(raw_offer.source_name)
            if normalizer is None:
                logger.warning(
                    "No normalizer is configured for job source; source=%s",
                    raw_offer.source_name,
                )
                continue
            try:
                offers.append(normalizer.normalize(raw_offer))
            except NormalizationError as exc:
                logger.warning(
                    "Job offer normalization failed; source=%s error_type=%s",
                    raw_offer.source_name,
                    type(exc).__name__,
                )
        return offers
