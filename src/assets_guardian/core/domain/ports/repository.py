from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any


class IRepository(ABC):
    """Port: Raw data repository access.

    Defines the contract for retrieving raw data
    from an external source (API, database, etc.).
    """

    @abstractmethod
    def get_raw_users(self) -> Iterable[dict[str, Any]]:
        """Retrieves the raw list of users."""
        raise NotImplementedError

    @abstractmethod
    def get_raw_assets(self) -> Iterable[dict[str, Any]]:
        """Retrieves the raw list of assets (projects, sites, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def get_raw_accesses(self) -> Iterable[dict[str, Any]]:
        """Retrieves the raw list of accesses/permissions."""
        raise NotImplementedError
