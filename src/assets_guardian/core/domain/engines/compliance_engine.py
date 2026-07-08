import logging
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from assets_guardian.core.domain.models.finding import Finding, RuleCategory
from assets_guardian.core.domain.models.rules.rule import IRule

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """
    IAM compliance engine.

    Responsible for executing audit rules by category (comparison,
    compliance, matrix) on the collected data.

    Attributes:
        _rules: List of rule instances to evaluate.
    """

    def __init__(self, rules: list[IRule]) -> None:
        """
        Initializes the engine with a list of rules.

        Args:
            rules: List of rule instances to evaluate.
        """
        self._rules = rules

    def run_comparison(
        self, old_data: Mapping[str, Iterable[Any]], new_data: Mapping[str, Iterable[Any]]
    ) -> Iterator[Finding]:
        """Executes comparison rules in streaming mode.

        Args:
            old_data: Data extracted from the old state (e.g., previous Excel sheet).
            new_data: Freshly collected data.

        Yields:
            Finding: Detected discrepancies on the fly.
        """
        comparison_rules = [
            rule for rule in self._rules if rule.rule_category == RuleCategory.COMPARISON
        ]

        logger.debug("Evaluating %d comparison rule(s)...", len(comparison_rules))

        for rule in comparison_rules:
            try:
                yield from rule.evaluate(
                    old_entries=old_data.get(rule.target_entity, []),
                    new_entries=new_data.get(rule.target_entity, []),
                )
            except Exception:
                logger.exception("Error in comparison rule %s", rule.rule_id)

    def run_compliance(
        self, live_data: Mapping[str, Iterable[Any]], config: dict[str, Any]
    ) -> Iterator[Finding]:
        """Executes IAM compliance rules in streaming mode.

        Args:
            live_data: Data collected in real time.
            config: Configuration parameters (thresholds, etc.).

        Yields:
            Finding: Detected non-conformities on the fly.
        """

        compliance_rules = [
            rule for rule in self._rules if rule.rule_category == RuleCategory.COMPLIANCE
        ]

        logger.debug("Evaluating %d compliance rule(s)...", len(compliance_rules))

        for rule in compliance_rules:
            try:
                yield from rule.evaluate(
                    entries=live_data.get(rule.target_entity, []), config=config
                )
            except Exception:
                logger.exception("Error in compliance rule %s", rule.rule_id)

    def run_matrix(
        self,
        accesses: Iterable[Any],
        matrix: dict[tuple[str, str], str],
        profiles: dict[str, list[str]],
    ) -> Iterator[Finding]:
        """Executes matrix checks in streaming mode.

        Args:
            accesses: List of actual collected accesses.
            matrix: Dictionary representing the matrix (profile -> asset -> role).
            profiles: Mapping of employees to their expected profiles.

        Yields:
            Finding: Detected unauthorized or missing accesses.
        """

        matrix_rules = [rule for rule in self._rules if rule.rule_category == RuleCategory.MATRIX]

        logger.debug("Evaluating %d matrix rule(s)...", len(matrix_rules))

        for rule in matrix_rules:
            try:
                yield from rule.evaluate(accesses=accesses, matrix=matrix, profiles=profiles)
            except Exception:
                logger.exception("Error in matrix rule %s", rule.rule_id)

    def run_all(
        self,
        *,
        old_data: Mapping[str, Iterable[Any]] | None = None,
        new_data: Mapping[str, Iterable[Any]] | None = None,
        live_data: Mapping[str, Iterable[Any]] | None = None,
        config: dict[str, Any] | None = None,
        accesses: Iterable[Any] | None = None,
        matrix: dict[tuple[str, str], str] | None = None,
        profiles: dict[str, list[str]] | None = None,
    ) -> Iterator[Finding]:
        """
        Executes all rule categories and yields findings incrementally.

        Args:
            old_data: Comparison data (old state).
            new_data: Comparison data (new state).
            live_data: Data for standard compliance.
            config: Global rules configuration.
            accesses: Actual access data for matrix checks.
            matrix: Authorized rights matrix.
            profiles: User profiles mapping.

        Yields:
            Finding: All anomalies detected by all rules.
        """
        yield from self.run_comparison(old_data or {}, new_data or {})
        yield from self.run_compliance(live_data or {}, config or {})
        yield from self.run_matrix(accesses or [], matrix or {}, profiles or {})
