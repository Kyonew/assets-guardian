from dataclasses import dataclass
from datetime import datetime
from typing import Any

from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.validator import validate_field


@dataclass(frozen=True, slots=True, kw_only=True)
class Access:
    """Normalized representation of an access right or permission on an asset.

    Attributes:
        source: Source name (e.g., gitlab, microsoft365, dolibarr, etc.).
        access_type: Type of access (e.g., permission, group, etc.).
        name: Name of the permission or group (e.g., Maintainer, code, user.own.view, etc.).
        description: Description of the access.
        asset: The asset concerned by this access.
        state: State of the access (e.g., active, expired, etc.).
        start_at: Starting date of the access.
        ends_at: Expiration date of the access.
        comments: Internal comments or notes for Assets Guardian.
        metadata: Custom arbitrary metadata dict.
    """

    # Global
    source: str
    access_type: str
    name: str
    description: str | None = None

    # Asset
    asset: Asset | None = None

    # Statut
    state: str | None = None

    # Dates
    start_at: datetime | None = None
    ends_at: datetime | None = None

    # Divers
    comments: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        validate_field(self, "source", str)
        validate_field(self, "access_type", str)
        validate_field(self, "name", str)
        validate_field(self, "description", str, optional=True, empty=True)
        validate_field(self, "asset", Asset, optional=True)
        validate_field(self, "state", str, optional=True)
        validate_field(self, "start_at", datetime, optional=True)
        validate_field(self, "ends_at", datetime, optional=True)
        validate_field(self, "comments", str, optional=True, empty=True)
        validate_field(self, "metadata", dict, optional=True)
