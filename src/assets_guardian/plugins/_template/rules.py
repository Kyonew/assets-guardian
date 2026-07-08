from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.models.finding import Finding, RuleCategory, SeverityType
from assets_guardian.core.domain.models.rules.compliance import IComplianceRule
from assets_guardian.core.domain.registry.rule_registry import RuleRegistry


@RuleRegistry.register("TEMPLATE-001")
class TemplateExampleRule(IComplianceRule):
    """Template example rule checking for compliance anomalies."""

    rule_id = "TEMPLATE-001"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the rule using configurations supplied from the rules
        configuration YAML file.
        """
        self._name: str = kwargs.get("name", "Template Example Rule")
        self._description: str = kwargs.get(
            "description", "Description of the template rule check."
        )

    @property
    def rule_category(self) -> RuleCategory:
        return RuleCategory.COMPLIANCE

    @property
    def severity(self) -> SeverityType:
        return SeverityType.INFO

    @property
    def target_entity(self) -> str:
        """Target collection to evaluate: 'users', 'assets', or 'accesses'."""
        return "users"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def evaluate(  # type: ignore
        self, entries: Iterable[Any], config: dict[str, Any] | None = None
    ) -> Iterable[Finding]:
        """Evaluate the rules against target domain models and yield findings."""
        # TODO: Implement custom evaluation logic
        raise NotImplementedError("evaluate must be implemented by the rule")
