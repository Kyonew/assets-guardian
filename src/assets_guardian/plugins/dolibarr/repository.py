import logging
from typing import Any

from assets_guardian.core.clients.http_client import HttpClient

logger = logging.getLogger(__name__)

_DEFAULT_PARAMS = {"sortfield": "t.rowid", "sortorder": "ASC", "limit": "200"}


class DolibarrRepository:
    """Repository to access raw data from the Dolibarr REST API.

    The Dolibarr API returns lists of users and groups as JSON lists.
    User details and a user's groups require separate calls (N+1).
    """

    def __init__(self, client: HttpClient) -> None:
        self._client = client

    def get_raw_users(self) -> list[dict[str, Any]]:
        """Retrieves all Dolibarr users (without permissions).

        Returns:
            list[dict[str, Any]]: List of raw users, empty on error.
        """
        logger.debug("Fetching Dolibarr users...")
        try:
            response = self._client.get("/users", params=_DEFAULT_PARAMS)
        except Exception:
            logger.exception("Exception while fetching Dolibarr users")
            return []

        if response.status_code != 200:
            logger.error("Error fetching Dolibarr users: %d", response.status_code)
            return []

        data = response.json()
        return data if isinstance(data, list) else []

    def get_raw_user_details(self, user_id: int | str) -> dict[str, Any]:
        """Retrieves details of a user with their permissions.

        Args:
            user_id: User's Dolibarr identifier.

        Returns:
            dict[str, Any]: Detailed user data (with ``permissions``),
            empty on error.
        """
        logger.debug("Fetching details for Dolibarr user %s...", user_id)
        try:
            response = self._client.get(f"/users/{user_id}", params={"includepermissions": 1})
        except Exception:
            logger.exception("Exception while fetching details for %s", user_id)
            return {}

        if response.status_code != 200:
            logger.warning(
                "Unable to fetch details for user %s: %d",
                user_id,
                response.status_code,
            )
            return {}

        data = response.json()
        return data if isinstance(data, dict) else {}

    def get_raw_user_groups(self, user_id: int | str) -> list[dict[str, Any]]:
        """Retrieves groups for a Dolibarr user.

        Args:
            user_id: User's Dolibarr identifier.

        Returns:
            list[dict[str, Any]]: List of user groups, empty on error.
        """
        logger.debug("Fetching groups for Dolibarr user %s...", user_id)
        try:
            response = self._client.get(f"/users/{user_id}/groups")
        except Exception:
            logger.exception("Exception while fetching groups for %s", user_id)
            return []

        if response.status_code != 200:
            logger.warning(
                "Unable to fetch groups for user %s: %d",
                user_id,
                response.status_code,
            )
            return []

        data = response.json()
        # The API can return a dict {id: group} or a list
        if isinstance(data, dict):
            return list(data.values())
        return data if isinstance(data, list) else []

    def get_raw_groups(self) -> list[dict[str, Any]]:
        """Retrieves all Dolibarr groups.

        Returns:
            list[dict[str, Any]]: List of raw groups, empty on error.
        """
        logger.debug("Fetching Dolibarr groups...")
        try:
            response = self._client.get("/users/groups", params=_DEFAULT_PARAMS)
        except Exception:
            logger.exception("Exception while fetching Dolibarr groups")
            return []

        if response.status_code != 200:
            logger.error("Error fetching Dolibarr groups: %d", response.status_code)
            return []

        data = response.json()
        if isinstance(data, dict):
            return list(data.values())
        return data if isinstance(data, list) else []

    # --- IRepository interface methods ---

    def get_raw_assets(self) -> list[dict[str, Any]]:
        """Returns groups as assets (IRepository implementation).

        Returns:
            list[dict[str, Any]]: List of raw groups.
        """
        return self.get_raw_groups()

    def get_raw_accesses(self) -> list[dict[str, Any]]:
        """Not used: Dolibarr accesses are built per user in the collector.

        Returns:
            list[dict[str, Any]]: Empty list (ARCH-LIMIT, see DolibarrCollector).
        """
        # ARCH-LIMIT: The IRepository interface assumes a flat list of accesses, but Dolibarr
        # requires N+1 calls (one per user) to get groups and permissions.
        # The collector bypasses this method and builds accesses directly.
        return []
