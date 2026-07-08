import logging
from typing import Any, ClassVar

from assets_guardian.core.domain.ports.client import IClientProvider

logger = logging.getLogger(__name__)


class ClientProviderRegistry:
    """Registry for client providers (IClientProvider)."""

    __providers: ClassVar[dict[str, type[IClientProvider]]] = {}

    @classmethod
    def register(cls, source_name: str) -> Any:
        """Decorator to register a client provider.

        Args:
            source_name: Name of the source (e.g., 'gitlab', 'm365').

        Returns:
            The decorator function.
        """

        def decorator(client_cls: type[IClientProvider]) -> type[IClientProvider]:
            if source_name in cls.__providers:
                logger.warning(
                    "Client provider for '%s' is already registered and will be overwritten.",
                    source_name,
                )
            cls.__providers[source_name] = client_cls
            logger.debug("Client provider for '%s' registered.", source_name)
            return client_cls

        return decorator

    @classmethod
    def instantiates_clientprovider(
        cls, source_name: str, config: dict[str, Any]
    ) -> IClientProvider:
        """Instantiates a client provider for the specified source.

        Args:
            source_name: Name of the source.
            config: Instance configuration parameters.

        Returns:
            An instance of IClientProvider.

        Raises:
            KeyError: If no provider is registered for the specified source name.
        """
        if source_name not in cls.__providers:
            logger.error("No client provider registered for source: %s", source_name)
            raise KeyError(f"Source '{source_name}' unrecognized in ClientProviderRegistry.")

        client_cls = cls.__providers[source_name]
        return client_cls(config)
