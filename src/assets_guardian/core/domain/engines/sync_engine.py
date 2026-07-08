import logging
from typing import Any

from assets_guardian.core.cache.cache import CacheManager
from assets_guardian.core.domain.engines.collector_engine import CollectorEngine, CollectorResult
from assets_guardian.core.domain.models.context import AssetsGuardianMode

logger = logging.getLogger(__name__)


class SyncEngine:
    """Orchestrator for data synchronization.

    Attributes:
        collector_engine: Engine responsible for data collection.
        cache: Cache service.
    """

    collector_engine: CollectorEngine
    cache: CacheManager

    def __init__(self, cache: CacheManager | None = None) -> None:
        self.cache = cache or CacheManager()
        self.collector_engine = CollectorEngine(cache=self.cache)

    def run(self, collectors: list[Any]) -> dict[tuple[str, str], CollectorResult]:
        """Executes data collection for all provided collectors.

        Args:
            collectors: List of collector instances to run.

        Returns:
            dict[tuple[str, str], CollectorResult]: Data collection results.
        """

        # Initialize the results dictionary
        results: dict[tuple[str, str], CollectorResult] = {}

        if not collectors:
            logger.warning("No collectors provided to SyncEngine.")
            return results

        logger.info("Starting collection for %d collector(s)...", len(collectors))

        for collector in collectors:
            # Use a unique key to identify each collection instance
            key = (collector.source_name, collector.instance_id)
            results[key] = self.collector_engine.run_collect(
                collector, mode=AssetsGuardianMode.SYNC
            )

        logger.info("Collection completed for all sources.")
        return results
