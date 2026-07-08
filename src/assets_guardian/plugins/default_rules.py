import logging
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from typing import Any

from assets_guardian.core.domain.models.finding import Finding, RuleCategory, SeverityType
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.models.rules.compliance import IComplianceRule
from assets_guardian.core.domain.registry.rule_registry import RuleRegistry

logger = logging.getLogger(__name__)


@RuleRegistry.register("DEFAULT-001")
class MultiFactorAuthRule(IComplianceRule):
    """Verifies that MFA (Multi-Factor Authentication) is enabled for all users.

    Attributes:
        rule_id: Unique rule identifier (DEFAULT-001).
    """

    rule_id: str = "DEFAULT-001"

    def __init__(self, **kwargs: Any) -> None:
        """Retrieves rule configuration from YAML.

        Args:
            **kwargs: Variable arguments containing 'name' and 'description'.
        """

        self.__name = kwargs.get("name", "MFA disabled")
        self.__description = kwargs.get(
            "description",
            "Multi-Factor Authentication must be enabled for user accounts.",
        )

    @property
    def rule_category(self) -> RuleCategory:
        return RuleCategory.COMPLIANCE

    @property
    def severity(self) -> SeverityType:
        return SeverityType.DANGER

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return str(self.__name)

    @property
    def description(self) -> str:
        return str(self.__description)

    def evaluate(  # type: ignore
        self, entries: Iterable[Identity], config: dict[Any, Any] | None = None
    ) -> Iterable[Finding]:
        """Inspects identities to detect absence of MFA.

        Args:
            entries: List of identities to analyze.
            config: Optional configuration (containing instance_id, etc.).

        Yields:
            Finding: A finding for each user without MFA.
        """
        for identity in entries:
            # If mfa_enabled is False, generate a finding
            if identity.mfa_enabled is False:
                yield Finding(
                    rule_id=self.rule_id,
                    rule_category=self.rule_category,
                    severity=self.severity,
                    title=self.name,
                    description=(
                        f"MFA is not enabled for user '{identity.name}' "
                        f"({identity.email or identity.username})."
                    ),
                    source=identity.source,
                    instance_id=(config or {}).get("instance_id", "unknown"),
                    entities_impacted=[identity.name],
                    metadata={
                        "external_id": identity.external_id,
                        "email": identity.email,
                        "username": identity.username,
                    },
                )


@RuleRegistry.register("DEFAULT-002")
class InactivityRule(IComplianceRule):
    """Verifies if an account has exceeded the allowed inactivity threshold.

    Attributes:
        rule_id: Unique rule identifier (DEFAULT-002).
    """

    rule_id: str = "DEFAULT-002"

    def __init__(self, **kwargs: Any) -> None:
        self.__name = kwargs.get("name", "Prolonged inactivity")
        self.__description = kwargs.get(
            "description", "The account has had no activity for a long time."
        )

        self.__warning_threshold_days = int(kwargs.get("inactivity_threshold_days_warning", 90))
        self.__danger_threshold_days = int(kwargs.get("inactivity_threshold_days_danger", 180))
        self.__critical_threshold_days = int(kwargs.get("inactivity_threshold_days_critical", 365))

    @property
    def rule_category(self) -> RuleCategory:
        return RuleCategory.COMPLIANCE

    @property
    def severity(self) -> SeverityType:
        return SeverityType.DANGER

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return str(self.__name)

    @property
    def description(self) -> str:
        return str(self.__description)

    def evaluate(  # type: ignore
        self, entries: Iterable[Identity], config: dict[Any, Any] | None = None
    ) -> Iterable[Finding]:
        """Compares the last activity with the configured threshold.

        Args:
            entries: List of identities to analyze.
            config: Optional configuration.

        Yields:
            Finding: A finding for each user inactive for too long.
        """
        now = datetime.now(UTC)

        threshold_warning = timedelta(days=self.__warning_threshold_days)
        threshold_danger = timedelta(days=self.__danger_threshold_days)
        threshold_critical = timedelta(days=self.__critical_threshold_days)

        for identity in entries:
            if identity.last_activity_at:
                dynamique_severity: SeverityType = self.severity
                raise_finding: bool = False

                # Ensure last_activity_at has timezone info for comparison
                last_activity = identity.last_activity_at
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=UTC)

                inactive_days = now - last_activity

                if inactive_days > threshold_warning:
                    dynamique_severity = SeverityType.WARNING
                    raise_finding = True

                if inactive_days > threshold_danger:
                    dynamique_severity = SeverityType.DANGER
                    raise_finding = True

                if inactive_days > threshold_critical:
                    dynamique_severity = SeverityType.CRITICAL
                    raise_finding = True

                if raise_finding:
                    yield Finding(
                        rule_id=self.rule_id,
                        rule_category=self.rule_category,
                        severity=dynamique_severity,
                        title=self.name,
                        description=(
                            f"User '{identity.name}' has had no activity for "
                            f"{inactive_days.days} days (last activity: "
                            f"{last_activity.strftime('%Y-%m-%d')})."
                        ),
                        source=identity.source,
                        instance_id=(config or {}).get("instance_id", "unknown"),
                        entities_impacted=[identity.name],
                        metadata={
                            "last_activity_at": last_activity.isoformat(),
                            "warning_threshold_days": self.__warning_threshold_days,
                            "danger_threshold_days": self.__danger_threshold_days,
                            "critical_threshold_days": self.__critical_threshold_days,
                        },
                    )


@RuleRegistry.register("DEFAULT-003")
class ExcessivePermissionsRule(IComplianceRule):
    """Verifies if an account possesses high privileges.

    Attributes:
        rule_id: Unique rule identifier (DEFAULT-003).
    """

    rule_id: str = "DEFAULT-003"

    def __init__(self, **kwargs: Any) -> None:
        self.__name = kwargs.get("name", "Excessive permissions")
        self.__description = kwargs.get(
            "description", "The account possesses administrative or high privileges."
        )

    @property
    def rule_category(self) -> RuleCategory:
        return RuleCategory.COMPLIANCE

    @property
    def severity(self) -> SeverityType:
        return SeverityType.DANGER

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return str(self.__name)

    @property
    def description(self) -> str:
        return str(self.__description)

    def evaluate(  # type: ignore
        self, entries: Iterable[Identity], config: dict[Any, Any] | None = None
    ) -> Iterable[Finding]:
        """Verifies if an account possesses high privileges.

        Args:
            entries: List of identities to analyze.
            config: Optional configuration.

        Yields:
            Finding: A finding for each privileged user.
        """
        for identity in entries:
            if identity.is_privileged is True:
                yield Finding(
                    rule_id=self.rule_id,
                    rule_category=self.rule_category,
                    severity=self.severity,
                    title=self.name,
                    description=f"User '{identity.name}' possesses excessive privileges.",
                    source=identity.source,
                    instance_id=(config or {}).get("instance_id", "unknown"),
                    entities_impacted=[identity.name],
                    metadata={"is_privileged": True},
                )


@RuleRegistry.register("DEFAULT-004")
class UnusualLocationRule(IComplianceRule):
    """Verifies if the last sign-in comes from an unusual IP (outside the company network).

    Attributes:
        rule_id: Unique rule identifier (DEFAULT-004).
    """

    rule_id: str = "DEFAULT-004"

    def __init__(self, **kwargs: Any) -> None:
        self.__name = kwargs.get("name", "Unusual sign-in location")
        self.__description = kwargs.get(
            "description", "The latest sign-in comes from an IP outside the company network."
        )
        self.__company_ip = kwargs.get("company_network_ip")

    @property
    def rule_category(self) -> RuleCategory:
        return RuleCategory.COMPLIANCE

    @property
    def severity(self) -> SeverityType:
        return SeverityType.WARNING

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return str(self.__name)

    @property
    def description(self) -> str:
        return str(self.__description)

    def evaluate(  # type: ignore
        self, entries: Iterable[Identity], config: dict[Any, Any] | None = None
    ) -> Iterable[Finding]:
        if not self.__company_ip:
            return

        try:
            company_ip = ip_address(self.__company_ip)
        except ValueError:
            logger.warning("Invalid company IP configured for DEFAULT-004: {self.__company_ip}")
            return

        for identity in entries:
            if identity.last_sign_in_ip and identity.last_sign_in_ip != company_ip:
                yield Finding(
                    rule_id=self.rule_id,
                    rule_category=self.rule_category,
                    severity=self.severity,
                    title=self.name,
                    description=(
                        f"User '{identity.name}' signed in from an "
                        f"unusual IP: {identity.last_sign_in_ip}."
                    ),
                    source=identity.source,
                    instance_id=(config or {}).get("instance_id", "unknown"),
                    entities_impacted=[identity.name],
                    metadata={"last_sign_in_ip": str(identity.last_sign_in_ip)},
                )
