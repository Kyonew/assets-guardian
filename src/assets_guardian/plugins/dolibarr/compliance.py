from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.models.finding import Finding, RuleCategory, SeverityType
from assets_guardian.core.domain.models.identity import Identity, IdentityState
from assets_guardian.core.domain.models.rules.compliance import IComplianceRule
from assets_guardian.core.domain.registry.rule_registry import RuleRegistry


@RuleRegistry.register("DOLIBARR-005")
class DolibarrDeactivatedUsersRule(IComplianceRule):
    """Lists disabled user accounts in Dolibarr.

    An account is considered disabled if its `statut` field is "0" in the Dolibarr API,
    which is mapped to IdentityState.INACTIVE during collection.
    """

    rule_id: str = "DOLIBARR-005"

    def __init__(self, **kwargs: Any) -> None:
        self.__name: str = kwargs.get("name", "Disabled user accounts")
        self.__description: str = kwargs.get(
            "description",
            "Lists user accounts whose status is deactivated in Dolibarr.",
        )
        self.__severity = SeverityType(kwargs.get("severity", SeverityType.INFO))
        self.instance_id: str = kwargs.get("instance_id", "default")

    @property
    def rule_category(self) -> RuleCategory:
        return RuleCategory.COMPLIANCE

    @property
    def severity(self) -> SeverityType:
        return self.__severity

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    def evaluate(  # type: ignore
        self,
        entries: Iterable[Identity],
        config: dict[Any, Any] | None = None,  # noqa: ARG002
    ) -> Iterable[Finding]:
        for identity in entries:
            if identity.state != IdentityState.INACTIVE:
                continue
            yield Finding(
                rule_id=self.rule_id,
                rule_category=self.rule_category,
                severity=self.severity,
                title=f"Disabled account: {identity.name}",
                description=(
                    f"Account '{identity.name}' ({identity.email or identity.username}) "
                    f"is disabled in Dolibarr (status=0)."
                ),
                source="dolibarr",
                instance_id=self.instance_id,
                entities_impacted=[identity.name],
                metadata={
                    "external_id": identity.external_id,
                    "email": identity.email,
                    "username": identity.username,
                },
            )
