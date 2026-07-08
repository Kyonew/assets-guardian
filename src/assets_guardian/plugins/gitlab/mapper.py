import logging
from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity, IdentityState, IdentityType
from assets_guardian.core.domain.ports.mapper import IMapper
from assets_guardian.plugins.gitlab.constants import ROLES_MAP, SOURCE_NAME
from assets_guardian.utils.dates import parse_datetime
from assets_guardian.utils.ip import parse_ip

logger = logging.getLogger(__name__)


class GitlabMapper(IMapper):
    """Mapper for GitLab.

    Transforms raw data from the GitLab API (via python-gitlab or directly)
    into normalized data models of the Assets Guardian domain.
    """

    def __init__(self, instance_id: str) -> None:
        """Initializes the mapper.

        Args:
            instance_id: Identifier of the source GitLab instance.
        """
        self._instance_id = instance_id

    @property
    def source_name(self) -> str:
        """Source name."""
        return SOURCE_NAME

    @property
    def instance_id(self) -> str:
        """Instance identifier."""
        return self._instance_id

    def to_identity(self, raw_data: Any, accesses: list[Access] | None = None) -> Identity:
        """Converts raw GitLab user data into an Identity object.

        Args:
            raw_data: Raw user data (dict).
            accesses: Optional list of accesses already collected for this user.

        Returns:
            An Identity instance.
        """
        if not isinstance(raw_data, dict):
            logger.warning("raw_data is not a dictionary: %s", type(raw_data))
            raw_data = {}

        return Identity(
            source=self.source_name,
            external_id=str(raw_data.get("id", "unknown")),
            identity_type=self.__map_identity_type(raw_data),
            name=raw_data.get("name") or raw_data.get("username") or "Unnamed",
            email=raw_data.get("email"),
            username=raw_data.get("username"),
            state=self.__map_identity_state(raw_data),
            mfa_enabled=raw_data.get("two_factor_enabled"),
            is_privileged=raw_data.get("is_admin"),
            is_external=raw_data.get("external"),
            created_at=parse_datetime(raw_data.get("created_at")),
            created_by=(
                raw_data.get("created_by", {}).get("name")
                if isinstance(raw_data.get("created_by"), dict)
                else raw_data.get("created_by")
            ),
            last_activity_at=parse_datetime(raw_data.get("last_activity_on")),
            last_sign_in_at=parse_datetime(raw_data.get("last_sign_in_at")),
            last_sign_in_ip=parse_ip(raw_data.get("last_sign_in_ip")),
            metadata={
                "web_url": raw_data.get("web_url"),
                "bot": raw_data.get("bot", False),
                "organization": raw_data.get("organization"),
                "current_sign_in_at": parse_datetime(raw_data.get("current_sign_in_at")),
                "current_sign_in_ip": parse_ip(raw_data.get("current_sign_in_ip")),
            },
            access=accesses,
        )

    def to_asset(self, raw_data: Any, asset_type: str = "unknown") -> Asset:
        """Converts raw GitLab project or group data into an Asset object.

        Args:
            raw_data: Raw project or group data (dict).
            asset_type: Asset type ("project" or "group").

        Returns:
            An Asset instance.
        """
        if not isinstance(raw_data, dict):
            raw_data = {}

        # Get path according to the type (direct and straightforward)
        if asset_type == "project":
            path = raw_data.get("path_with_namespace")
        elif asset_type == "group":
            path = raw_data.get("full_path")
        else:
            path = raw_data.get("path", "unknown")

        metadata = {
            "path": path,
            "web_url": raw_data.get("web_url"),
            "visibility": raw_data.get("visibility"),
        }

        # For projects, retrieve namespace (parent group) info
        if asset_type == "project" and isinstance(raw_data.get("namespace"), dict):
            namespace = raw_data["namespace"]
            metadata.update(
                {
                    "parent_id": str(namespace.get("id", "unknown")),
                    "parent_name": namespace.get("name", "Unnamed Group"),
                }
            )

        return Asset(
            source=self.source_name,
            external_id=str(raw_data.get("id", "unknown")),
            asset_type=asset_type,
            name=raw_data.get("name", "Unnamed Asset"),
            description=raw_data.get("description"),
            state="archived" if raw_data.get("archived") else "active",
            created_at=parse_datetime(raw_data.get("created_at")),
            metadata=metadata,
        )

    def to_access(
        self, raw_data: Any, asset: Asset | None = None, user_info: dict[str, Any] | None = None
    ) -> Access:
        """Converts raw GitLab permission data into an Access object.

        Args:
            raw_data: Raw permission/member data (dict).
            asset: The asset (Project or Group) to which this access relates.
            user_info: Optional user information (dict).

        Returns:
            An Access instance.
        """
        if not isinstance(raw_data, dict):
            raw_data = {}

        access_level = raw_data.get("access_level", 0)

        metadata = {
            "access_level": access_level,
        }

        if user_info:
            metadata.update(
                {
                    "user_external_id": str(user_info.get("id", "unknown")),
                    "user_name": user_info.get("name") or user_info.get("username") or "Unnamed",
                    "user_username": user_info.get("username"),
                    "user_email": user_info.get("email"),
                }
            )

        if asset:
            metadata.update(
                {
                    "asset_external_id": asset.external_id,
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type,
                }
            )
            # If the asset has a parent (e.g. project in a group), add it
            if asset.metadata:
                metadata.update(
                    {
                        "asset_parent_id": asset.metadata.get("parent_id"),
                        "asset_parent_name": asset.metadata.get("parent_name"),
                    }
                )

        return Access(
            source=self.source_name,
            access_type="role",
            name=ROLES_MAP.get(access_level, f"Unknown ({access_level})"),
            asset=asset,
            state="active",
            start_at=parse_datetime(raw_data.get("created_at")),
            ends_at=parse_datetime(raw_data.get("expires_at")),
            metadata=metadata,
        )

    def __map_identity_type(self, raw_data: dict[str, Any]) -> IdentityType:
        """Determines if the user is a human or a bot.

        Args:
            raw_data: Raw user data.

        Returns:
            The identity type (HUMAN or NON_HUMAN).
        """
        if raw_data.get("bot"):
            return IdentityType.NON_HUMAN

        # also check the username for bots
        username = str(raw_data.get("username", "")).lower()
        if "_bot_" in username:
            return IdentityType.NON_HUMAN

        return IdentityType.HUMAN

    def __map_identity_state(self, raw_data: dict[str, Any]) -> IdentityState:
        """Maps GitLab state to IdentityState.

        Args:
            raw_data: Raw user data.

        Returns:
            The identity state (ACTIVE, BLOCKED, etc.).
        """
        state = str(raw_data.get("state", "active")).lower()
        if state == "active":
            return IdentityState.ACTIVE
        if state == "blocked":
            return IdentityState.BLOCKED
        return IdentityState.INACTIVE
