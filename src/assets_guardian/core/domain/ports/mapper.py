from abc import ABC, abstractmethod
from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity


class IMapper(ABC):
    """Port: Data normalizer (mapper).

    Defines the contract for converting raw data from APIs
    to the domain's normalized data models.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique source name (must match config.yml)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def instance_id(self) -> str:
        """The specific instance identifier (e.g., 'main', 'prod')."""
        raise NotImplementedError

    @abstractmethod
    def to_identity(self, raw_data: Any) -> Identity:
        """Converts raw data to an Identity object."""
        raise NotImplementedError

    @abstractmethod
    def to_asset(self, raw_data: Any) -> Asset:
        """Converts raw data to an Asset object."""
        raise NotImplementedError

    @abstractmethod
    def to_access(self, raw_data: Any, asset: Asset | None = None) -> Access:
        """Converts raw data to an Access object."""
        raise NotImplementedError
