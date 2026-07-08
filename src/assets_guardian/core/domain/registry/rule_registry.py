import logging
from typing import Any, ClassVar

from assets_guardian.core.domain.models.rules.rule import IRule

logger = logging.getLogger(__name__)


class RuleRegistry:
    """Registry for audit rules.

    Allows registering and retrieving rules by their identifier,
    managing namespaces (e.g., 'DEFAULT', 'gitlab').

    Attributes:
        __rules: Nested dictionary [source][rule_id] storing rule classes.
    """

    __rules: ClassVar[dict[str, dict[str, type[IRule]]]] = {}

    @classmethod
    def register(cls, rule_id: str) -> Any:
        """Decorator to register a rule in the registry.

        Args:
            rule_id: Unique identifier of the rule (e.g., 'DEFAULT-001').

        Returns:
            Any: The class decorator function.
        """

        def decorator(rule_cls: type[IRule]) -> type[IRule]:
            module_name = rule_cls.__module__

            # Source detection (e.g., assets_guardian.plugins.gitlab -> gitlab)
            source = module_name.split(".")[2].lower() if "plugins." in module_name else "default"

            # Normalization: default_rules -> default
            if source == "default_rules":
                source = "default"

            # Initialize source namespace
            if source not in cls.__rules:
                cls.__rules[source] = {}

            # Registration
            cls.__rules[source][rule_id.upper()] = rule_cls

            logger.debug("Rule registered: %s:%s", source, rule_id)
            return rule_cls

        return decorator

    @classmethod
    def get_rule(cls, rule_id: str, source: str = "default") -> type[IRule]:
        """Retrieves a rule class from the registry.

        Args:
            rule_id: Identifier of the rule.
            source: Source of the rule (e.g., 'gitlab', 'default').

        Returns:
            type[IRule]: The requested rule class.

        Raises:
            KeyError: If the rule is not found in the source or fallback.
        """
        source = source.lower()
        rule_id = rule_id.upper()

        # Search in the specified source
        if source in cls.__rules and rule_id in cls.__rules[source]:
            return cls.__rules[source][rule_id]

        # Fallback to DEFAULT
        if source != "default" and "default" in cls.__rules and rule_id in cls.__rules["default"]:
            return cls.__rules["default"][rule_id]

        logger.error("Rule not found: %s:%s", source, rule_id)
        raise KeyError(f"Rule '{rule_id}' unrecognized for source '{source}'.")

    @classmethod
    def get_all(cls) -> dict[str, dict[str, type[IRule]]]:
        """Returns all rule classes grouped by source.

        Returns:
            dict: Dictionary {source: {rule_id: rule_cls}}.
        """
        return cls.__rules

    @classmethod
    def clear(cls) -> None:
        """Clears the registry (useful for testing)."""
        cls.__rules = {}
