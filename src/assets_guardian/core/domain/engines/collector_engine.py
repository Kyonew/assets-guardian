import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from assets_guardian.core.cache.cache import CacheManager
from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.context import AssetsGuardianMode
from assets_guardian.core.domain.models.identity import Identity

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectorResult:
    """Result of a single collector execution.

    Attributes:
        source_name: Name of the source (e.g., 'gitlab').
        instance_id: ID of the collection instance (e.g., 'prod').
        identities: Iterable of collected identities.
        assets: Iterable of collected assets.
        accesses: Iterable of collected access data.
        success: Flag indicating if the collection succeeded.
        error: Error message if the collection failed.
    """

    source_name: str
    instance_id: str
    identities: Iterable[Identity] = field(default_factory=list)
    assets: Iterable[Asset] = field(default_factory=list)
    accesses: Iterable[Access] = field(default_factory=list)
    success: bool = True
    error: str | None = None


class CollectorEngine:
    """IAM collection engine with checkpoint (caching) support."""

    cache: CacheManager

    def __init__(self, cache: CacheManager | None = None) -> None:
        self.cache = cache or CacheManager()

    def run_collect(self, collector: Any, mode: AssetsGuardianMode) -> CollectorResult:
        """Runs a collector with checkpoint (caching) support.

        For each data type, checks if it is already present in the cache;
        if not, triggers a live collection.

        Args:
            collector: The collector instance to execute.
            mode: The command mode ('sync' or 'audit') used to determine the cache namespace.

        Returns:
            CollectorResult: The result containing collected data or failure info.
        """

        source_name = collector.source_name
        instance_id = collector.instance_id
        key = f"[{source_name}:{instance_id}]"

        mode_str = mode.value

        # Backup file paths
        identities_path: Path = self.cache.get_file_path(
            mode_str, source_name, instance_id, "identities"
        )
        assets_path: Path = self.cache.get_file_path(mode_str, source_name, instance_id, "assets")
        accesses_path: Path = self.cache.get_file_path(
            mode_str, source_name, instance_id, "accesses"
        )

        try:
            # IDENTITIES
            if self.cache.has_checkpoint(identities_path):
                logger.info(
                    "%s [%s] Identities already cached, restoring from backup...", key, mode_str
                )
            else:
                logger.info("%s [%s] Collecting identities...", key, mode_str)
                self.cache.save(collector.collect_identities(), identities_path)

            identities = self.cache.load_iterable(identities_path, Identity)

            # ASSETS
            if self.cache.has_checkpoint(assets_path):
                logger.info("%s Assets already cached, restoring from backup...", key)
            else:
                logger.info("%s Collecting assets...", key)
                self.cache.save(collector.collect_assets(), assets_path)

            assets = self.cache.load_iterable(assets_path, Asset)

            # ACCESSES
            if self.cache.has_checkpoint(accesses_path):
                logger.info("%s Access data already cached, restoring from backup...", key)
            else:
                logger.info("%s Collecting access data...", key)
                self.cache.save(collector.collect_accesses(), accesses_path)

            accesses = self.cache.load_iterable(accesses_path, Access)

            return CollectorResult(
                source_name=source_name,
                instance_id=instance_id,
                identities=identities,
                assets=assets,
                accesses=accesses,
                success=True,
            )

        except Exception as e:
            logger.exception("%s [%s] Collection failed", key, mode_str)
            return CollectorResult(
                source_name=source_name,
                instance_id=instance_id,
                success=False,
                error=str(e),
            )
