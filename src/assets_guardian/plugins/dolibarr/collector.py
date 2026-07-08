import logging
from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.ports.collector import Collector
from assets_guardian.core.domain.registry.collector_registry import CollectorRegistry
from assets_guardian.plugins.dolibarr.constants import (
    CRITICAL_MODULES,
    DEFAULT_INSTANCE_ID,
    MODULE_LABELS,
    SOURCE_NAME,
)
from assets_guardian.plugins.dolibarr.mapper import DolibarrMapper
from assets_guardian.plugins.dolibarr.repository import DolibarrRepository

logger = logging.getLogger(__name__)


@CollectorRegistry.register(SOURCE_NAME)
class DolibarrCollector(Collector):
    """Dolibarr Collector.

    ARCH-LIMIT: The Collector base class assumes that collect_identities(),
    collect_assets() and collect_accesses() are independent. For Dolibarr,
    accesses (groups and permissions) require N+1 calls per user.
    Therefore, we completely override these three methods and share an assets cache
    to avoid redundant calls.
    """

    def __init__(self, client: Any, instance_config: dict[str, Any]) -> None:
        self.__client = client
        self.__config = instance_config
        base_url = instance_config.get("url")
        self.__mapper = DolibarrMapper(instance_id=self.instance_id, base_url=base_url)
        self.__repository = DolibarrRepository(client)
        self._assets_cache: dict[str, Asset] | None = None
        self._raw_groups: list[dict[str, Any]] = []
        self._group_accesses_cache: list[Access] | None = None

    @property
    def source_name(self) -> str:
        return SOURCE_NAME

    @property
    def instance_id(self) -> str:
        return str(self.__config.get("instance_id", DEFAULT_INSTANCE_ID))

    def collect_identities(self) -> list[Identity]:
        """Collects all Dolibarr users with their groups and critical permissions.

        Each user requires two additional calls:
        - /users/{id}?includepermissions=1 → module-level permissions
        - /users/{id}/groups → group memberships

        ARCH-LIMIT: This N+1 pattern is not supported by the base class
        nor by the IRepository interface, which assumes a flat list of accesses.

        Returns:
            list[Identity]: List of collected identities with their accesses.
        """
        raw_users = self.__repository.get_raw_users()
        identities = []

        for raw_user in raw_users:
            user_id = raw_user.get("id")
            if not user_id:
                continue

            detailed_user = self.__repository.get_raw_user_details(user_id)
            full_user = {**raw_user, **detailed_user}

            accesses = self.__build_accesses_for_user(user_id, full_user)
            identity = self.__mapper.to_identity(full_user, accesses=accesses)
            identities.append(identity)

        logger.info("Collected %d Dolibarr identities.", len(identities))
        return identities

    def collect_assets(self) -> list[Asset]:
        """Collects all Dolibarr groups and critical modules as assets.

        Returns:
            list[Asset]: List of collected assets (groups and virtual modules).
        """
        raw_groups = self.__repository.get_raw_groups()
        self._raw_groups = raw_groups
        assets = [self.__mapper.to_asset(g) for g in raw_groups]

        # Add virtual assets for critical modules
        for module in CRITICAL_MODULES:
            label = MODULE_LABELS.get(module, module.capitalize())
            assets.append(
                Asset(
                    source=self.source_name,
                    external_id=f"module_{module}",
                    asset_type="module",
                    name=f"Module {label}",
                    description=f"Critical Dolibarr module: {label}",
                    state="active",
                )
            )

        self._assets_cache = {str(a.external_id): a for a in assets}
        logger.info("Collected %d Dolibarr assets (groups and modules).", len(assets))
        return assets

    def collect_accesses(self) -> list[Access]:
        """Returns all accesses extracted from identities and groups.

        Accesses include:
        - Group memberships (access_type="group")
        - Direct/effective user permissions (access_type="module_permission")
        - Permissions granted by groups (access_type="group_permission")

        Returns:
            list[Access]: Consolidated list of all Dolibarr accesses.
        """
        identities = self.collect_identities()
        all_accesses: list[Access] = []
        for identity in identities:
            if identity.access:
                all_accesses.extend(identity.access)

        # Extract access statistics
        num_groups = sum(1 for a in all_accesses if a.access_type == "group")
        user_level_perms = sum(1 for a in all_accesses if a.access_type == "module_permission")

        logger.info(
            "Dolibarr: %d group accesses, %d direct/effective user permissions.",
            num_groups,
            user_level_perms,
        )

        group_perms = self.__collect_group_permissions(identities)
        all_accesses.extend(group_perms)

        logger.info("Extracted %d Dolibarr accesses in total.", len(all_accesses))
        return all_accesses

    # --- Internal methods ---

    def __find_asset(self, group_id: Any) -> Asset | None:
        """Finds an asset in the cache by its external identifier.

        Args:
            group_id: External identifier of the asset to search.

        Returns:
            Asset | None: The matching asset, or None if not found.
        """
        if group_id is None:
            return None
        if self._assets_cache is None:
            self.collect_assets()
        return self._assets_cache.get(str(group_id)) if self._assets_cache else None

    def __build_accesses_for_user(self, user_id: Any, full_user: dict[str, Any]) -> list[Access]:
        """Builds the access list for a user (groups + critical permissions).

        Args:
            user_id: User's Dolibarr identifier.
            full_user: Full user data including permissions.

        Returns:
            list[Access]: List of user's accesses.
        """
        accesses: list[Access] = []

        # Group memberships
        raw_groups = self.__repository.get_raw_user_groups(user_id)
        for raw_group in raw_groups:
            group_id = raw_group.get("id")
            asset = self.__find_asset(group_id)
            accesses.append(self.__mapper.to_access(raw_group, asset=asset, user_info=full_user))

        # Permissions on critical modules (stored in user details)
        permissions: dict[str, Any] = full_user.get("rights") or full_user.get("permissions") or {}
        accesses.extend(self.__extract_critical_module_accesses(permissions, full_user))

        return accesses

    def __extract_critical_module_accesses(
        self, permissions: dict[str, Any], user_info: dict[str, Any]
    ) -> list[Access]:
        """Extracts rights on critical modules as Access objects.

        Only modules declared in CRITICAL_MODULES are transformed.
        Nested permissions (e.g. user.user.lire) are flattened at the first level.
        Each permission is attached to its corresponding virtual module Asset.

        Args:
            permissions: Dictionary of user permissions, indexed by module.
            user_info: Full user data.

        Returns:
            list[Access]: Access objects of type ``module_permission`` for active rights.
        """
        accesses: list[Access] = []
        for module, module_perms in permissions.items():
            if module not in CRITICAL_MODULES or not isinstance(module_perms, dict):
                continue

            # Retrieve virtual asset for this module
            asset = self.__find_asset(f"module_{module}")

            for perm_key, perm_value in module_perms.items():
                if isinstance(perm_value, dict):
                    # Nested permissions (e.g. user.user.lire, user.self.creer)
                    for sub_key, sub_value in perm_value.items():
                        if str(sub_value) == "1":
                            accesses.append(
                                self.__mapper.to_module_permission_access(
                                    module=f"{module}.{perm_key}",
                                    permission_key=sub_key,
                                    user_info=user_info,
                                    asset=asset,
                                )
                            )
                elif str(perm_value) == "1":
                    accesses.append(
                        self.__mapper.to_module_permission_access(
                            module=module,
                            permission_key=perm_key,
                            user_info=user_info,
                            asset=asset,
                        )
                    )
        return accesses

    def __get_user_permissions(self, identities: list[Identity]) -> dict[str, set[tuple[str, str]]]:
        """Maps each user to the set of their module_permission accesses."""
        user_perms = {}
        for identity in identities:
            uid = str(identity.external_id)
            perms = set()
            for a in identity.access or []:
                if a.access_type == "module_permission" and a.metadata:
                    raw_mod = a.metadata.get("raw_module")
                    raw_pk = a.metadata.get("raw_permission_key")
                    if raw_mod and raw_pk:
                        perms.add((raw_mod, raw_pk))
            user_perms[uid] = perms
        return user_perms

    def __get_group_members(self, identities: list[Identity]) -> dict[str, list[str]]:
        """Maps each group to the list of its active members."""
        group_members: dict[str, list[str]] = {}
        for identity in identities:
            uid = str(identity.external_id)
            for a in identity.access or []:
                if a.access_type == "group":
                    meta = a.metadata or {}
                    gid = str(a.asset.external_id) if a.asset else str(meta.get("group_id", ""))
                    if gid:
                        group_members.setdefault(gid, []).append(uid)
        return group_members

    def __collect_group_permissions(self, identities: list[Identity]) -> list[Access]:
        """Collects permissions on modules granted by each Dolibarr group.

        Reconstructs group permissions by calculating the intersection of the
        effective rights of all their active members.
        """
        if self._group_accesses_cache is not None:
            return self._group_accesses_cache

        if self._assets_cache is None:
            self.collect_assets()

        user_perms = self.__get_user_permissions(identities)
        group_members = self.__get_group_members(identities)
        raw_groups_by_id = {str(g.get("id", "")): g for g in self._raw_groups}
        group_accesses: list[Access] = []

        for asset in (self._assets_cache or {}).values():
            if asset.asset_type != "group":
                continue

            group_id = str(asset.external_id)
            members = group_members.get(group_id)

            if not members:
                logger.info("Group %s ('%s') has no active members.", group_id, asset.name)
                continue

            # Intersection of permissions of all active group members
            common_perms = set.intersection(*(user_perms.get(uid, set()) for uid in members))

            raw_group = raw_groups_by_id.get(group_id, {})
            for raw_mod, raw_pk in common_perms:
                group_accesses.append(
                    self.__mapper.to_group_permission_access(
                        group_info=raw_group,
                        module=raw_mod,
                        permission_key=raw_pk,
                        asset=asset,
                    )
                )

        self._group_accesses_cache = group_accesses
        logger.info("Collected %d Dolibarr group permissions.", len(group_accesses))
        return group_accesses
