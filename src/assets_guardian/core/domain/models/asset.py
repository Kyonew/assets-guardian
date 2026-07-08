from dataclasses import dataclass
from datetime import datetime
from typing import Any

from assets_guardian.core.domain.models.validator import validate_field


@dataclass(frozen=True, slots=True, kw_only=True)
class Asset:
    """Normalized representation of an asset (resource) from an external source.

    Attributes:
        source: Source name (e.g., gitlab, microsoft365, dolibarr, etc.).
        external_id: Unique identifier of the asset within the source.
        asset_type: Type of asset (e.g., repository, group, mailbox, etc.).
        name: Name of the asset in the source.
        description: Description of the asset in the source.
        state: State of the asset in the source (e.g., active, archived, etc.).
        created_at: Creation date of the asset in the source.
        created_by: Identifier of the asset's creator in the source.
        comments: Internal comments or notes for Assets Guardian.
        metadata: Custom arbitrary metadata dict.
    """

    # Global
    source: str
    external_id: str
    asset_type: str

    # Infos
    name: str
    description: str | None = None

    # Status
    state: str | None = None

    # Dates and origin
    created_at: datetime | None = None
    created_by: str | None = None

    # Miscellaneous
    comments: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        validate_field(self, "source", str)
        validate_field(self, "external_id", str)
        validate_field(self, "asset_type", str)
        validate_field(self, "name", str)
        validate_field(self, "description", str, optional=True, empty=True)
        validate_field(self, "state", str, optional=True)
        validate_field(self, "created_at", datetime, optional=True)
        validate_field(self, "created_by", str, optional=True)
        validate_field(self, "comments", str, optional=True, empty=True)
        validate_field(self, "metadata", dict, optional=True)
