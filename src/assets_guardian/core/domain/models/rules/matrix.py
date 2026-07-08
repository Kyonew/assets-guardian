from abc import abstractmethod
from collections.abc import Iterable

from assets_guardian.core.domain.models.finding import Finding, RuleCategory
from assets_guardian.core.domain.models.rules.rule import IRule


class IMatrixRule(IRule):
    @property
    def rule_category(self) -> RuleCategory:
        """Rule category: MATRIX (matrix rules)."""
        return RuleCategory.MATRIX

    @abstractmethod
    def evaluate(self, accesses: Iterable, matrix: dict, profiles: dict) -> Iterable[Finding]:  # type: ignore
        """Verifies compliance of effective accesses with the matrix.

        Args:
            accesses: List of actual collected accesses.
            matrix: Matrix dictionary (profile -> asset -> role).
            profiles: Mapping of employees to their expected profiles.

        Returns:
            Iterable[Finding]: List of detected discrepancies.
        """
        raise NotImplementedError
