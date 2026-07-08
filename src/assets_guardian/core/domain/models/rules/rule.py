from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.models.finding import Finding, RuleCategory, SeverityType


class IRule(ABC):
    """Base interface for all audit rules."""

    rule_id: str = ""

    @property
    @abstractmethod
    def rule_category(self) -> RuleCategory:
        """Category of the rule."""
        raise NotImplementedError

    @property
    @abstractmethod
    def severity(self) -> SeverityType:
        """Severity level of the rule."""
        raise NotImplementedError

    @property
    @abstractmethod
    def target_entity(self) -> str:
        """Entity targeted by the rule."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the rule."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the rule."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, **kwargs: Any) -> Iterable[Finding]:
        """Evaluates the rule on the provided data."""
        raise NotImplementedError
