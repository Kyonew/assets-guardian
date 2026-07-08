import logging
from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.models.finding import Finding, SeverityType
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.models.rules.comparison import IComparisonRule
from assets_guardian.core.domain.registry.rule_registry import RuleRegistry

logger = logging.getLogger(__name__)


def _index_users(users: Iterable[Identity]) -> dict[str, Identity]:
    return {u.external_id: u for u in users if u.external_id}


@RuleRegistry.register("COMPARE-001")
class DolibarrNewUserComparisonRule(IComparisonRule):
    """Detects new users created in Dolibarr."""

    rule_id: str = "COMPARE-001"

    def __init__(self, **kwargs: Any) -> None:
        self.instance_id = kwargs.get("instance_id", "default")
        self._name = kwargs.get("name", "Dolibarr user additions")
        self._description = kwargs.get(
            "description", "Detects the creation of new accounts in Dolibarr."
        )
        self._severity = kwargs.get("severity", SeverityType.INFO)

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def severity(self) -> SeverityType:
        return SeverityType(self._severity)

    @property
    def name(self) -> str:
        return str(self._name)

    @property
    def description(self) -> str:
        return str(self._description)

    def evaluate(  # type: ignore
        self, old_entries: Iterable[Identity], new_entries: Iterable[Identity]
    ) -> Iterable[Finding]:
        old_entries_list = list(old_entries)
        if not old_entries_list:
            old_entries_list = list(self.load_baseline())

        old_users = _index_users(old_entries_list)
        new_users = _index_users(new_entries)

        for user_id, new_user in new_users.items():
            if user_id not in old_users:
                yield Finding(
                    rule_id=self.rule_id,
                    rule_category=self.rule_category,
                    severity=self.severity,
                    title=f"New Dolibarr user: {new_user.name}",
                    description=(
                        f"User '{new_user.name}' ({new_user.email or new_user.username}) "
                        f"was created in Dolibarr."
                    ),
                    source="dolibarr",
                    instance_id=self.instance_id,
                    entities_impacted=[new_user.name],
                    metadata={
                        "external_id": new_user.external_id,
                        "email": new_user.email,
                        "username": new_user.username,
                        "state": str(new_user.state) if new_user.state else None,
                    },
                )


@RuleRegistry.register("COMPARE-002")
class DolibarrDeletedUserComparisonRule(IComparisonRule):
    """Detects users deleted from Dolibarr."""

    rule_id: str = "COMPARE-002"

    def __init__(self, **kwargs: Any) -> None:
        self.instance_id = kwargs.get("instance_id", "default")
        self._name = kwargs.get("name", "Dolibarr user deletions")
        self._description = kwargs.get("description", "Detects account deletions in Dolibarr.")
        self._severity = kwargs.get("severity", SeverityType.WARNING)

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def severity(self) -> SeverityType:
        return SeverityType(self._severity)

    @property
    def name(self) -> str:
        return str(self._name)

    @property
    def description(self) -> str:
        return str(self._description)

    def evaluate(  # type: ignore
        self, old_entries: Iterable[Identity], new_entries: Iterable[Identity]
    ) -> Iterable[Finding]:
        old_entries_list = list(old_entries)
        if not old_entries_list:
            old_entries_list = list(self.load_baseline())

        old_users = _index_users(old_entries_list)
        new_users = _index_users(new_entries)

        for user_id, old_user in old_users.items():
            if user_id not in new_users:
                yield Finding(
                    rule_id=self.rule_id,
                    rule_category=self.rule_category,
                    severity=self.severity,
                    title=f"User deleted from Dolibarr: {old_user.name}",
                    description=(
                        f"User '{old_user.name}' ({old_user.email or old_user.username}) "
                        f"was deleted from Dolibarr."
                    ),
                    source="dolibarr",
                    instance_id=self.instance_id,
                    entities_impacted=[old_user.name],
                    metadata={
                        "external_id": old_user.external_id,
                        "email": old_user.email,
                        "username": old_user.username,
                    },
                )
