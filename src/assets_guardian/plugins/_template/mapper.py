from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.ports.mapper import IMapper

from .constants import SOURCE_NAME


class TemplateMapper(IMapper):
    """Mapper responsible for transforming raw data into strongly-typed domain models."""

    def __init__(self, instance_id: str) -> None:
        self._instance_id = instance_id

    @property
    def source_name(self) -> str:
        return SOURCE_NAME

    @property
    def instance_id(self) -> str:
        return self._instance_id

    def to_identity(self, raw_data: Any) -> Identity:
        """Transform a raw user record into an Identity domain model."""
        # TODO: Map raw_data dictionary fields to Identity properties
        raise NotImplementedError("to_identity must be implemented by the mapper")

    def to_asset(self, raw_data: Any) -> Asset:
        """Transform a raw asset record into an Asset domain model."""
        # TODO: Map raw_data dictionary fields to Asset properties
        raise NotImplementedError("to_asset must be implemented by the mapper")

    def to_access(self, raw_data: Any, asset: Asset | None = None) -> Access:
        """Transform a raw access record into an Access domain model."""
        # TODO: Map raw_data dictionary fields to Access properties
        raise NotImplementedError("to_access must be implemented by the mapper")
