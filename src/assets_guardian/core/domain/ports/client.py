from abc import ABC, abstractmethod
from typing import Any

from assets_guardian.core.clients.http_client import HttpClient
from assets_guardian.core.clients.mysql_client import MySQLClient


class IClientProvider(ABC):
    """Port: Client provider used to collect data.

    Defines the contract for obtaining a client
    specific to a data source.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the client provider with the instance's configuration dictionary."""
        raise NotImplementedError

    @abstractmethod
    def instantiate_client(self) -> HttpClient | MySQLClient | Any:
        """Returns a ready-to-use client.

        The return type depends on the specific implementation (e.g., GraphServiceClient,
        requests Session, GitLab client, etc.).
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies that the client connection, return True if the remote service is reachable and credentials are valid, else False."""  # noqa: E501
        raise NotImplementedError
