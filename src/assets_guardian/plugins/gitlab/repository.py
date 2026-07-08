import logging
from typing import Any

from assets_guardian.core.clients.http_client import HttpClient

logger = logging.getLogger(__name__)


class GitlabRepository:
    """Repository to access raw data from the GitLab API.

    Uses HttpClient to perform requests to the API v4.
    """

    def __init__(self, client: HttpClient) -> None:
        """Initializes the repository with an HTTP client.

        Args:
            client: HttpClient instance configured for the GitLab API.
        """
        self._client = client

    def get_raw_users(self) -> list[dict[str, Any]]:
        """Retrieves all GitLab users.

        Returns:
            List of raw dictionaries representing users.
        """
        logger.debug("Fetching GitLab users...")
        try:
            response = self._client.get("/users", params={"per_page": 100})
        except Exception:
            logger.exception("Exception while fetching users")
            return []

        if response.status_code != 200:
            logger.error("Error while fetching users: %d", response.status_code)
            return []

        data: list[dict[str, Any]] = response.json()
        return data

    def get_raw_user_details(self, user_id: int | str) -> dict[str, Any]:
        """Retrieves details of a specific user (necessary for IPs etc).

        Args:
            user_id: GitLab user identifier.

        Returns:
            Raw dictionary representing user details.
        """
        logger.debug("Fetching details for user %s...", user_id)
        try:
            response = self._client.get(f"/users/{user_id}")
        except Exception:
            logger.exception("Exception while fetching details for %s", user_id)
            return {}

        if response.status_code != 200:
            logger.error(
                "Error while fetching details for %s: %d",
                user_id,
                response.status_code,
            )
            return {}

        data: dict[str, Any] = response.json()
        return data

    def get_raw_projects(self) -> list[dict[str, Any]]:
        """Retrieves all accessible GitLab projects.

        Returns:
            List of raw dictionaries representing projects.
        """
        logger.debug("Fetching GitLab projects...")
        try:
            response = self._client.get("/projects", params={"per_page": 100})
        except Exception:
            logger.exception("Exception while fetching projects")
            return []

        if response.status_code != 200:
            logger.error("Error while fetching projects: %d", response.status_code)
            return []

        data: list[dict[str, Any]] = response.json()
        return data

    def get_raw_groups(self) -> list[dict[str, Any]]:
        """Retrieves all accessible GitLab groups.

        Returns:
            List of raw dictionaries representing groups.
        """
        logger.debug("Fetching GitLab groups...")
        try:
            response = self._client.get("/groups", params={"per_page": 100})
        except Exception:
            logger.exception("Exception while fetching groups")
            return []

        if response.status_code != 200:
            logger.error("Error while fetching groups: %d", response.status_code)
            return []

        data: list[dict[str, Any]] = response.json()
        return data

    def get_accesses_for_user(self, user_id: int | str) -> list[dict[str, Any]]:
        """Retrieves memberships of a user to projects and groups.

        Args:
            user_id: GitLab user identifier.

        Returns:
            List of memberships with a 'pid' field added to match the collector's expectations.
        """
        logger.debug("Fetching accesses for user %s...", user_id)
        try:
            response = self._client.get(f"/users/{user_id}/memberships", params={"per_page": 100})
        except Exception:
            logger.exception("Exception while fetching accesses for %s", user_id)
            return []

        if response.status_code != 200:
            logger.warning(
                "Unable to fetch accesses for user %s: %d",
                user_id,
                response.status_code,
            )
            return []

        memberships: list[dict[str, Any]] = response.json()
        # Normalize by adding 'pid' since the collector expects this field
        for membership in memberships:
            membership["pid"] = membership.get("source_id")

        return memberships
