from typing import Any

from assets_guardian.core.clients.http_client import HttpClient
from assets_guardian.core.clients.mysql_client import MySQLClient
from assets_guardian.core.domain.ports.client import IClientProvider
from assets_guardian.core.domain.registry.client_registry import ClientProviderRegistry

from .constants import SOURCE_NAME


@ClientProviderRegistry.register(SOURCE_NAME)
class TemplateClientProvider(IClientProvider):
    """Client provider for the template plugin."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def instantiate_client(self) -> HttpClient | MySQLClient | Any:
        """Return a configured client instance (e.g. HttpClient)."""
        # TODO: Implement client instantiation using self._config
        raise NotImplementedError("instantiate_client must be implemented by the plugin")

    def health_check(self) -> bool:
        """Verify that the connection is active and credentials are valid."""
        # TODO: Implement health check logic
        raise NotImplementedError("health_check must be implemented by the plugin")
