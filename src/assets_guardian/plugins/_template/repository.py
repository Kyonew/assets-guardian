from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.ports.repository import IRepository


class TemplateRepository(IRepository):
    """Repository responsible for fetching raw data from the external source."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def get_raw_users(self) -> Iterable[dict[str, Any]]:
        """Fetch and return raw user/identity records from the external source."""
        # TODO: Retrieve raw users using self._client
        raise NotImplementedError("get_raw_users must be implemented by the repository")

    def get_raw_assets(self) -> Iterable[dict[str, Any]]:
        """Fetch and return raw asset records from the external source."""
        # TODO: Retrieve raw assets using self._client
        raise NotImplementedError("get_raw_assets must be implemented by the repository")

    def get_raw_accesses(self) -> Iterable[dict[str, Any]]:
        """Fetch and return raw membership/access records from the external source."""
        # TODO: Retrieve raw accesses using self._client
        raise NotImplementedError("get_raw_accesses must be implemented by the repository")
