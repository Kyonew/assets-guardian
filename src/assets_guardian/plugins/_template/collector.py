import logging
from typing import Any

from assets_guardian.core.domain.ports.collector import Collector
from assets_guardian.core.domain.registry.collector_registry import CollectorRegistry

from .constants import SOURCE_NAME
from .mapper import TemplateMapper
from .repository import TemplateRepository

logger = logging.getLogger(__name__)


@CollectorRegistry.register(SOURCE_NAME)
class TemplateCollector(Collector):
    """Collector orchestrating raw data fetching and mapping for the template plugin."""

    def __init__(self, client: Any, instance_config: dict[str, Any]) -> None:
        super().__init__(client, instance_config)
        self._mapper = TemplateMapper(instance_id=self.instance_id)
        self._repository = TemplateRepository(client)

    @property
    def source_name(self) -> str:
        return SOURCE_NAME

    @property
    def instance_id(self) -> str:
        return str(self._config.get("instance_id", ""))

    # Note: Base Collector implements collect_identities, collect_assets, and collect_accesses.
    # Override them here only if you need advanced custom logic or orchestration.
