import logging
from typing import Any

from assets_guardian.core.domain.registry.client_registry import ClientProviderRegistry
from assets_guardian.core.domain.registry.collector_registry import CollectorRegistry

logger = logging.getLogger(__name__)


def instantiate_collectors(
    integrations_config: dict[str, dict[str, Any]],
) -> dict[tuple[str, str], Any]:
    """Instantiates all configured collectors.

    Args:
        integrations_config: Dictionary of integrations from AppConfig.

    Returns:
        dict[tuple[str, str], Any]: Dictionary mapping each tuple
        (source name, instance identifier) to its collector instance.
        Collectors that failed to instantiate are omitted.
    """
    collectors: dict[tuple[str, str], Any] = {}

    for source_name, instances in integrations_config.items():
        for instance_id, params in instances.items():
            if params is None:
                params = {}
            if "instance_id" not in params:
                params["instance_id"] = instance_id
            key = (source_name, instance_id)
            try:
                # Attempt to obtain a client via the client provider registry
                client = None
                try:
                    client_provider = ClientProviderRegistry.instantiates_clientprovider(
                        source_name, params
                    )
                    client = client_provider.instantiate_client()
                    logger.debug("%s:%s : Client created", source_name, instance_id)
                except KeyError:
                    logger.warning(
                        "%s:%s : No client provider found, using client=None",
                        source_name,
                        instance_id,
                    )

                collector = CollectorRegistry.instantiates_collector(
                    source_name, client=client, instance_config=params
                )
                collectors[key] = collector
                logger.debug("%s:%s : Instantiation successful", source_name, instance_id)

            except KeyError:
                logger.exception("%s:%s : Plugin not found", source_name, instance_id)
            except Exception:
                logger.exception("%s:%s : Error during initialization", source_name, instance_id)

    return collectors
