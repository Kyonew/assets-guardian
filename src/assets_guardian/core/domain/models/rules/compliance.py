from abc import abstractmethod
from collections.abc import Iterable

from assets_guardian.core.domain.models.finding import Finding, RuleCategory
from assets_guardian.core.domain.models.rules.rule import IRule


class IComplianceRule(IRule):
    @property
    def rule_category(self) -> RuleCategory:
        """Rule category: COMPLIANCE (compliance rules)."""
        return RuleCategory.COMPLIANCE

    @abstractmethod
    def evaluate(self, entries: Iterable, config: dict | None = None) -> Iterable[Finding]:  # type: ignore
        """Inspects a list of entries to detect non-conformities.

        Args:
            entries: List of entries (identities OR accesses) to analyze.
            config: Optional parameters (thresholds, network IPs, etc.) from YAML.

        Returns:
            Iterable[Finding]: List of detected non-conformities.
        """
        raise NotImplementedError
