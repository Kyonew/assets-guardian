import logging
from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity, IdentityState, IdentityType
from assets_guardian.core.domain.ports.mapper import IMapper
from assets_guardian.plugins.dolibarr.constants import (
    CRITICAL_MODULES,
    SOURCE_NAME,
    get_permission_label,
)
from assets_guardian.utils.dates import parse_datetime
from assets_guardian.utils.ip import parse_ip

logger = logging.getLogger(__name__)


class DolibarrMapper(IMapper):
    """Mapper for Dolibarr.

    Transforms raw data from the Dolibarr REST API into normalized models
    of the Assets Guardian domain.

    Architectural choices:
    - Dolibarr groups -> Asset(asset_type="group")
    - Group membership -> Access(access_type="group", asset=<group>)
    - User rights on critical modules -> Access(access_type="module_permission", asset=<module>)
    - Rights granted by a group -> Access(access_type="group_permission", asset=<group>)

    """

    def __init__(self, instance_id: str, base_url: str | None = None) -> None:
        self._instance_id = instance_id
        self._base_url = base_url

    @property
    def source_name(self) -> str:
        return SOURCE_NAME

    @property
    def instance_id(self) -> str:
        return self._instance_id

    def __clean_field(self, val: Any) -> Any:
        """Returns the value or None if it is falsy."""
        return val or None

    def __extract_permissions(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Extracts permissions/rights from the user's raw dictionary."""
        perms = raw_data.get("rights") or raw_data.get("permissions")
        return perms if isinstance(perms, dict) else {}

    def __extract_mfa(self, raw_data: dict[str, Any]) -> bool:
        """Determines if multi-factor authentication (MFA) is enabled."""
        opts = raw_data.get("array_options") or {}
        return bool(opts.get("options_totp2fa_secret"))

    def __build_metadata(
        self,
        raw_data: dict[str, Any],
        permissions: dict[str, Any],
    ) -> dict[str, Any]:
        """Builds standard metadata for an identity."""
        meta = {
            "permissions": permissions,
            "entity": raw_data.get("entity"),
            "datec": raw_data.get("datec"),
            "previous_sign_in_at": parse_datetime(raw_data.get("datepreviouslogin")),
            "previous_sign_in_ip": raw_data.get("ippreviouslogin"),
        }
        if self._base_url:
            meta["web_url"] = self._base_url
        return meta

    def to_identity(self, raw_data: Any, accesses: list[Access] | None = None) -> Identity:
        """Converts a Dolibarr user into an Identity.

        The `statut` field indicates the state ("1" = active, "0" = inactive).
        The `admin` field indicates the superadmin status (1 = yes, 0 = no).

        Args:
            raw_data: Raw dictionary from the Dolibarr API representing a user.
            accesses: List of accesses already built for this user.

        Returns:
            Identity: The normalized identity.
        """
        if not isinstance(raw_data, dict):
            raw_data = {}

        permissions = self.__extract_permissions(raw_data)
        mfa_enabled = self.__extract_mfa(raw_data)
        job = raw_data.get("job")
        metadata = self.__build_metadata(raw_data, permissions)

        return Identity(
            source=self.source_name,
            external_id=str(raw_data.get("id", "unknown")),
            identity_type=IdentityType.HUMAN,
            name=self.__full_name(raw_data),
            first_name=self.__clean_field(raw_data.get("firstname")),
            last_name=self.__clean_field(raw_data.get("lastname")),
            email=self.__clean_field(raw_data.get("email")),
            username=self.__clean_field(raw_data.get("login")),
            mfa_enabled=mfa_enabled,
            description=self.__clean_field(job),
            state=self.__state(raw_data),
            is_privileged=self.__is_privileged(raw_data),
            created_at=parse_datetime(raw_data.get("datec")),
            last_sign_in_at=parse_datetime(raw_data.get("datelastlogin")),
            last_sign_in_ip=parse_ip(raw_data.get("iplastlogin")),
            access=accesses,
            metadata=metadata,
        )

    @staticmethod
    def __full_name(raw_data: dict[str, Any]) -> str:
        firstname = raw_data.get("firstname") or ""
        lastname = raw_data.get("lastname") or ""
        return f"{firstname} {lastname}".strip() or raw_data.get("login") or "Unnamed"

    @staticmethod
    def __state(raw_data: dict[str, Any]) -> IdentityState:
        active = str(raw_data.get("statut", "0")) == "1"
        return IdentityState.ACTIVE if active else IdentityState.INACTIVE

    @staticmethod
    def __is_privileged(raw_data: dict[str, Any]) -> bool:
        return bool(int(raw_data.get("admin", 0) or 0))

    def to_asset(self, raw_data: Any, asset_type: str = "group") -> Asset:
        """Converts a Dolibarr group into an Asset.

        Args:
            raw_data: Raw dictionary from the Dolibarr API representing a group.
            asset_type: Type of asset to use (default: ``"group"``).

        Returns:
            Asset: The normalized asset.
        """
        if not isinstance(raw_data, dict):
            raw_data = {}

        return Asset(
            source=self.source_name,
            external_id=str(raw_data.get("id", "unknown")),
            asset_type=asset_type,
            name=raw_data.get("name") or "Unnamed Group",
            description=raw_data.get("note") or None,
            created_at=parse_datetime(raw_data.get("datec", "")),
            metadata={
                "entity": raw_data.get("entity"),
                **({"web_url": self._base_url} if self._base_url else {}),
            },
        )

    def __populate_user_metadata(self, user_info: dict[str, Any]) -> dict[str, Any]:
        """Extracts user metadata for access."""
        first = user_info.get("firstname") or ""
        last = user_info.get("lastname") or ""
        full = f"{first} {last}".strip()
        if not full:
            full = user_info.get("login") or "Unnamed"

        is_admin_raw = user_info.get("admin")
        if not is_admin_raw:
            is_admin_raw = 0

        return {
            "user_external_id": str(user_info.get("id", "unknown")),
            "user_name": full,
            "user_username": user_info.get("login"),
            "user_email": user_info.get("email"),
            "is_admin": bool(int(is_admin_raw)),
        }

    def to_access(
        self,
        raw_data: Any,
        asset: Asset | None = None,
        user_info: dict[str, Any] | None = None,
    ) -> Access:
        """Converts a Dolibarr group membership into an Access.

        The access represents the fact that a user belongs to a group.
        The group is the target asset.

        Args:
            raw_data: Raw group dictionary returned by the Dolibarr API.
            asset: Asset associated with the group, if available.
            user_info: Full data of the user who is a member of the group.

        Returns:
            Access: Normalized access representing group membership.
        """
        raw = raw_data if isinstance(raw_data, dict) else {}
        group_name = raw.get("name") or (asset.name if asset else "Unknown Group")
        group_id = raw.get("id") or (asset.external_id if asset else None)
        desc = raw.get("note") or (asset.description if asset else None)

        metadata = {"group_id": group_id, "group_name": group_name}
        if user_info:
            metadata.update(self.__populate_user_metadata(user_info))

        return Access(
            source=self.source_name,
            access_type="group",
            name=group_name,
            description=desc,
            asset=asset,
            state="active",
            start_at=parse_datetime(raw.get("datec")),
            metadata=metadata,
        )

    def to_module_permission_access(
        self,
        module: str,
        permission_key: str,
        user_info: dict[str, Any],
        asset: Asset | None = None,
    ) -> Access:
        """Creates an Access representing a user right on a Dolibarr module.

        The access is linked to the virtual Asset of the corresponding module.

        Args:
            module: Dolibarr module name (e.g. ``"banque"``, ``"user.user"``).
            permission_key: Permission key (e.g. ``"lire"``, ``"creer"``).
            user_info: Full user data.
            asset: Virtual module Asset, if available.

        Returns:
            Access: Normalized access of type ``module_permission``.
        """
        user_name = (
            f"{user_info.get('firstname', '')} {user_info.get('lastname', '')}".strip()
            or user_info.get("login")
            or "Unnamed"
        )
        permission_label = get_permission_label(module, permission_key)

        module_last = module.split(".")[-1]
        permission_last = permission_key.split(".")[-1]

        metadata: dict[str, Any] = {
            "module": module_last,
            "permission_key": permission_last,
            "permission_label": permission_label,
            "raw_module": module,
            "raw_permission_key": permission_key,
            "is_critical": module.split(".")[0] in CRITICAL_MODULES,
            "user_external_id": str(user_info.get("id", "unknown")),
            "user_name": user_name,
            "user_username": user_info.get("login"),
            "user_email": user_info.get("email"),
        }
        if asset:
            metadata.update(
                {
                    "asset_external_id": asset.external_id,
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type,
                }
            )
        return Access(
            source=self.source_name,
            access_type="module_permission",
            name=permission_last,
            asset=asset,
            state="active",
            metadata=metadata,
        )

    def to_group_permission_access(
        self,
        group_info: dict[str, Any],
        module: str,
        permission_key: str,
        asset: Asset | None = None,
        api_label: str = "",
    ) -> Access:
        """Creates an Access representing a permission granted by a Dolibarr group.

        A virtual asset of type ``"group_permission"`` is created so that
        the ``GenericSheetBuilder`` can filter using ``filter_by_asset_type``.

        Args:
            group_info: Raw group dictionary returned by the Dolibarr API.
            module: Dolibarr module name (e.g. ``"banque"``, ``"facture"``).
            permission_key: Permission key (e.g. ``"lire"``, ``"creer"``).
            asset: Asset of the group granting the permission (ignored, kept for compatibility).
            api_label: Label provided by the Dolibarr API (prioritized over local dictionary).

        Returns:
            Access: Normalized access of type ``group_permission``.
        """
        group_name = group_info.get("name") or (asset.name if asset else "Unknown Group")
        group_id = group_info.get("id") or (asset.external_id if asset else None)
        permission_label = api_label or get_permission_label(module, permission_key)

        module_last = module.split(".")[-1]
        permission_last = permission_key.split(".")[-1]

        virtual_asset = Asset(
            source=self.source_name,
            external_id=f"group_{group_id}",
            asset_type="group_permission",
            name=group_name,
            description=f"Permissions of group {group_name}",
        )

        return Access(
            source=self.source_name,
            access_type="group_permission",
            name=permission_last,
            asset=virtual_asset,
            state="active",
            metadata={
                "group_id": group_id,
                "group_name": group_name,
                "module": module_last,
                "permission_key": permission_last,
                "permission_label": permission_label,
            },
        )
