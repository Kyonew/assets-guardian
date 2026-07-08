from typing import Any

import pytest

from assets_guardian.core.domain.models.finding import Finding
from assets_guardian.core.domain.models.rules.rule import IRule
from assets_guardian.core.domain.registry.rule_registry import RuleRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    RuleRegistry.clear()
    yield
    RuleRegistry.clear()


def test_rule_registry_register_and_get():
    # Simulate a plugin rule by setting __module__
    class TestRule(IRule):
        def evaluate(self, **kwargs: Any) -> list[Finding]:
            return []

    TestRule.__module__ = "assets_guardian.plugins.gitlab.rules"

    RuleRegistry.register("001")(TestRule)

    # Check listing (via get_all)
    all_rules = RuleRegistry.get_all()
    assert "gitlab" in all_rules
    assert "001" in all_rules["gitlab"]

    # Get rule class
    rule_cls = RuleRegistry.get_rule("001", source="gitlab")
    assert rule_cls == TestRule


def test_rule_registry_case_insensitivity():
    class TestRule(IRule):
        def evaluate(self, **kwargs: Any) -> list[Finding]:
            return []

    TestRule.__module__ = "assets_guardian.plugins.custom.rules"
    RuleRegistry.register("abc")(TestRule)

    # Should be retrievable with different case
    assert RuleRegistry.get_rule("ABC", source="CUSTOM") == TestRule
    assert RuleRegistry.get_rule("abc", source="custom") == TestRule


def test_rule_registry_key_error():
    with pytest.raises(KeyError, match="Rule 'UNKNOWN' unrecognized for source 'default'"):
        RuleRegistry.get_rule("unknown")


def test_rule_registry_default_fallback():
    class DefaultRule(IRule):
        def evaluate(self, **kwargs: Any) -> list[Finding]:
            return []

    DefaultRule.__module__ = "assets_guardian.core.domain.models.rules.defaults"
    RuleRegistry.register("DEF-001")(DefaultRule)

    # Even if requested for gitlab, DEF-001 must return the DEFAULT rule
    assert RuleRegistry.get_rule("DEF-001", source="gitlab") == DefaultRule


def test_rule_registry_default_rules_normalization():
    class DefaultRule(IRule):
        def evaluate(self, **kwargs: Any) -> list[Finding]:
            return []

    DefaultRule.__module__ = "assets_guardian.plugins.default_rules.rules"
    RuleRegistry.register("DR-001")(DefaultRule)

    # Should be normalized to 'default'
    assert "default" in RuleRegistry.get_all()
    assert RuleRegistry.get_rule("DR-001", source="default") == DefaultRule


def test_rule_registry_multiple_rules_same_source():
    class R1(IRule):
        def evaluate(self, **kwargs: Any) -> list[Finding]:
            return []

    class R2(IRule):
        def evaluate(self, **kwargs: Any) -> list[Finding]:
            return []

    R1.__module__ = "assets_guardian.plugins.test.rules"
    R2.__module__ = "assets_guardian.plugins.test.rules"

    RuleRegistry.register("R1")(R1)
    RuleRegistry.register("R2")(R2)

    assert len(RuleRegistry.get_all()["test"]) == 2
