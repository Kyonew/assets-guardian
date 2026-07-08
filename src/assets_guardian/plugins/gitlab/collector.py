import logging
from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.ports.collector import Collector
from assets_guardian.core.domain.registry.collector_registry import CollectorRegistry
from assets_guardian.plugins.gitlab.constants import DEFAULT_INSTANCE_ID, SOURCE_NAME
from assets_guardian.plugins.gitlab.mapper import GitlabMapper
from assets_guardian.plugins.gitlab.repository import GitlabRepository

logger = logging.getLogger(__name__)


@CollectorRegistry.register(SOURCE_NAME)
class GitlabCollector(Collector):
    """GitLab collector using a repository."""

    def __init__(self, client: Any, instance_config: dict[str, Any]) -> None:
        """Initializes the GitLab collector.

        Args:
            client: GitLab API client instance (HttpClient).
            instance_config: GitLab instance specific configuration.
        """
        self.__client = client
        self.__config = instance_config
        self.__mapper = GitlabMapper(instance_id=self.instance_id)
        self.__repository = GitlabRepository(client)

        self._assets_cache: dict[str, Asset] | None = None

    @property
    def source_name(self) -> str:
        """Data source name."""
        return SOURCE_NAME

    @property
    def instance_id(self) -> str:
        """Unique identifier of the GitLab instance."""
        return str(self.__config.get("instance_id", DEFAULT_INSTANCE_ID))

    def collect_identities(self) -> list[Identity]:
        """Collects all identities (users) and their accesses from GitLab.

        Returns:
            List of normalized Identity objects.
        """

        raw_users = self.__repository.get_raw_users()

        # Prepare accesses for each user (cross-referencing data)
        identities = []
        for raw_user in raw_users:
            # Fetch details (essential for IPs, MFA, etc.)
            user_id: str | int = raw_user.get("id", "")
            detailed_user = self.__repository.get_raw_user_details(user_id) if user_id else {}

            # Merge (details take precedence over the list as they are more complete)
            full_raw_user = {**raw_user, **detailed_user}

            # Fetch raw accesses for this user
            raw_accesses = self.__repository.get_accesses_for_user(user_id)

            # Map these accesses to Access objects (passing raw user info for metadata)
            user_accesses = [
                self.__mapper.to_access(
                    raw_access,
                    asset=self.__find_asset(raw_access.get("pid")),
                    user_info=full_raw_user,
                )
                for raw_access in raw_accesses
            ]

            if detailed_user["is_admin"]:
                user_accesses.append(
                    self.__mapper.to_access(
                        {"access_level": "Administrator"},
                        asset=self.__find_asset("instance"),
                        user_info=full_raw_user,
                    )
                )

            # Create the final identity with ALL its data (including accesses).
            # Since Identity is immutable, we create it once here.
            identity = self.__mapper.to_identity(full_raw_user, accesses=user_accesses)

            identities.append(identity)

        return identities

    def __find_asset(self, external_id: Any) -> Asset | None:
        """Finds an Asset (Project or Group) by its GitLab ID in the cache.

        Args:
            external_id: GitLab external identifier of the asset.

        Returns:
            The corresponding Asset object or None if not found.
        """
        if external_id is None:
            return None

        if self._assets_cache is None:
            logger.info("Filling the GitLab asset mini cache...")
            assets = self.collect_assets()
            self._assets_cache = {str(a.external_id): a for a in assets}

        return self._assets_cache.get(str(external_id))

    def collect_assets(self) -> list[Asset]:
        """Collects all assets (projects and groups) from GitLab.

        Returns:
            List of normalized Asset objects.
        """
        raw_projects = self.__repository.get_raw_projects()
        raw_groups = self.__repository.get_raw_groups()

        assets = [self.__mapper.to_asset(p, asset_type="project") for p in raw_projects]
        assets.extend([self.__mapper.to_asset(g, asset_type="group") for g in raw_groups])
        assets.append(
            Asset(
                source=self.source_name,
                external_id="instance",
                asset_type="instance",
                name="Administrator",
            )
        )

        # Update the cache
        self._assets_cache = {str(a.external_id): a for a in assets}

        return assets

    def collect_accesses(self) -> list[Access]:
        """Retrieves all accesses already attached to the collected identities.

        Returns:
            Flat list of all Access objects found.
        """

        identities = self.collect_identities()

        # Extract all accesses into a flat list
        all_accesses = []
        for identity in identities:
            if identity.access:
                all_accesses.extend(identity.access)

        logger.info("Extracted %d accesses for GitLab.", len(all_accesses))
        return all_accesses
