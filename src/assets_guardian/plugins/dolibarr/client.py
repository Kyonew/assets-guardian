from typing import Any

from assets_guardian.core.clients.http_client import HttpClient
from assets_guardian.core.domain.ports.client import IClientProvider
from assets_guardian.core.domain.registry.client_registry import ClientProviderRegistry
from assets_guardian.plugins.dolibarr.constants import SOURCE_NAME


@ClientProviderRegistry.register(SOURCE_NAME)
class DolibarrClientProvider(IClientProvider):
    """Client provider for Dolibarr using HttpClient."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.__config = config

    def instantiate_client(self) -> HttpClient:
        """Returns an HttpClient configured with the Dolibarr DOLAPIKEY."""
        credentials = self.__config.get("credentials", {})
        dolapikey = credentials.get("dolapikey") or self.__config.get("dolapikey", "")
        base_url = self.__config.get("url", "").rstrip("/")
        headers = {"DOLAPIKEY": dolapikey, "Accept": "application/json"}
        return HttpClient(base_url=base_url, headers=headers)

    def health_check(self) -> bool:
        """Verifies that the connection to Dolibarr works and the API key is valid."""
        try:
            client = self.instantiate_client()
            response = client.get("/users/1")
        except Exception:
            return False
        else:
            return response.status_code == 200
