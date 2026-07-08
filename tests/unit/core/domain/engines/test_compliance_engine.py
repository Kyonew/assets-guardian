"""Tests for the compliance engine."""

from unittest.mock import MagicMock

from assets_guardian.core.domain.engines.compliance_engine import ComplianceEngine
from assets_guardian.core.domain.models.finding import Finding, RuleCategory
from assets_guardian.core.domain.models.rules.comparison import IComparisonRule
from assets_guardian.core.domain.models.rules.compliance import IComplianceRule
from assets_guardian.core.domain.models.rules.matrix import IMatrixRule


def test_compliance_engine_run_comparison():
    """Verify that comparison rules are correctly executed and their findings collected."""
    rule = MagicMock(spec=IComparisonRule)
    rule.rule_category = RuleCategory.COMPARISON
    rule.target_entity = "users"
    rule.rule_id = "COMP-001"
    finding = MagicMock(spec=Finding)
    rule.evaluate.return_value = [finding]

    engine = ComplianceEngine(rules=[rule])
    old_data = {"users": [1, 2]}
    new_data = {"users": [2, 3]}

    findings = list(engine.run_comparison(old_data, new_data))
    assert len(findings) == 1
    assert findings[0] == finding
    rule.evaluate.assert_called_once_with(old_entries=[1, 2], new_entries=[2, 3])


def test_compliance_engine_run_comparison_exception():
    """Verify that exceptions raised by comparison rules are gracefully handled and ignored."""
    rule = MagicMock(spec=IComparisonRule)
    rule.rule_category = RuleCategory.COMPARISON
    rule.target_entity = "users"
    rule.evaluate.side_effect = Exception("Test error")

    engine = ComplianceEngine(rules=[rule])
    findings = list(engine.run_comparison({"users": []}, {"users": []}))
    assert len(findings) == 0


def test_compliance_engine_run_compliance():
    """Verify that compliance rules evaluate live data with current configuration."""
    rule = MagicMock(spec=IComplianceRule)
    rule.rule_category = RuleCategory.COMPLIANCE
    rule.target_entity = "assets"
    finding = MagicMock(spec=Finding)
    rule.evaluate.return_value = [finding]

    engine = ComplianceEngine(rules=[rule])
    live_data = {"assets": ["a1"]}
    config = {"threshold": 10}

    findings = list(engine.run_compliance(live_data, config))
    assert len(findings) == 1
    assert findings[0] == finding
    rule.evaluate.assert_called_once_with(entries=["a1"], config=config)


def test_compliance_engine_run_compliance_exception():
    """Verify that exceptions raised by compliance rules are caught and handled."""
    rule = MagicMock(spec=IComplianceRule)
    rule.rule_category = RuleCategory.COMPLIANCE
    rule.target_entity = "assets"
    rule.evaluate.side_effect = Exception("Test error")

    engine = ComplianceEngine(rules=[rule])
    findings = list(engine.run_compliance({"assets": []}, {}))
    assert len(findings) == 0


def test_compliance_engine_run_matrix():
    """Verify that matrix rules evaluate access, matrix, and profile parameters correctly."""
    rule = MagicMock(spec=IMatrixRule)
    rule.rule_category = RuleCategory.MATRIX
    finding = MagicMock(spec=Finding)
    rule.evaluate.return_value = [finding]

    engine = ComplianceEngine(rules=[rule])
    accesses = []
    matrix = {}
    profiles = {}

    findings = list(engine.run_matrix(accesses, matrix, profiles))
    assert len(findings) == 1
    assert findings[0] == finding
    rule.evaluate.assert_called_once_with(accesses=accesses, matrix=matrix, profiles=profiles)


def test_compliance_engine_run_matrix_exception():
    """Verify that exceptions raised by matrix rules are caught and handled."""
    rule = MagicMock(spec=IMatrixRule)
    rule.rule_category = RuleCategory.MATRIX
    rule.evaluate.side_effect = Exception("Test error")

    engine = ComplianceEngine(rules=[rule])
    findings = list(engine.run_matrix([], {}, {}))
    assert len(findings) == 0


def test_compliance_engine_run_all():
    """Verify that all rule categories (comparison, compliance, matrix) are executed when run_all is called."""
    rules = []
    findings_sent = []
    for cat in [RuleCategory.COMPARISON, RuleCategory.COMPLIANCE, RuleCategory.MATRIX]:
        rule = MagicMock()
        rule.rule_category = cat
        rule.target_entity = "test"
        finding = MagicMock(spec=Finding)
        rule.evaluate.return_value = [finding]
        findings_sent.append(finding)
        rules.append(rule)

    engine = ComplianceEngine(rules=rules)
    results = list(engine.run_all())

    assert len(results) == 3
    assert results == findings_sent
