import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from assets_guardian.core.domain.models.finding import RuleCategory, SeverityType
from assets_guardian.core.domain.models.rules.comparison import IComparisonRule
from assets_guardian.core.domain.models.rules.compliance import IComplianceRule
from assets_guardian.core.domain.models.rules.matrix import IMatrixRule


class ConcreteComparisonRule(IComparisonRule):
    @property
    def severity(self) -> SeverityType:
        return SeverityType.INFO

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return "name"

    @property
    def description(self) -> str:
        return "desc"

    def evaluate(self, old_entries, new_entries):
        return []


class ConcreteComplianceRule(IComplianceRule):
    @property
    def severity(self) -> SeverityType:
        return SeverityType.INFO

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return "name"

    @property
    def description(self) -> str:
        return "desc"

    def evaluate(self, entries, config):
        return []


class ConcreteMatrixRule(IMatrixRule):
    @property
    def severity(self) -> SeverityType:
        return SeverityType.INFO

    @property
    def target_entity(self) -> str:
        return "users"

    @property
    def name(self) -> str:
        return "name"

    @property
    def description(self) -> str:
        return "desc"

    def evaluate(self, accesses, matrix, profiles):
        return []


def test_comparison_rule_category():
    rule = ConcreteComparisonRule()
    assert rule.rule_category == RuleCategory.COMPARISON
    # Can't instantiate abstract class directly, so we test evaluate on the concrete one
    assert rule.evaluate([], []) == []


def test_compliance_rule_category():
    rule = ConcreteComplianceRule()
    assert rule.rule_category == RuleCategory.COMPLIANCE
    assert rule.evaluate([], {}) == []


def test_matrix_rule_category():
    rule = ConcreteMatrixRule()
    assert rule.rule_category == RuleCategory.MATRIX
    assert rule.evaluate([], {}, {}) == []


# ---------------------------------------------------------------------------
# IComparisonRule.load_baseline(), full branch coverage
# ---------------------------------------------------------------------------


def test_load_baseline_no_excel_path_returns_empty_list() -> None:
    """load_baseline returns [] immediately when no excel_path is provided."""
    rule = ConcreteComparisonRule()
    result = list(rule.load_baseline(None))
    assert result == []


def test_load_baseline_no_config_path_returns_empty_list(tmp_path: Path) -> None:
    """load_baseline returns [] and warns when __resolve_config_path yields None."""
    rule = ConcreteComparisonRule()
    excel_file = tmp_path / "report.xlsx"
    excel_file.write_bytes(b"")

    with patch.object(rule, "_IComparisonRule__resolve_config_path", return_value=None):
        result = list(rule.load_baseline(excel_file))

    assert result == []


def test_load_baseline_no_sheet_name_returns_empty_list(tmp_path: Path) -> None:
    """load_baseline returns [] and warns when __resolve_sheet_name yields None."""
    rule = ConcreteComparisonRule()
    excel_file = tmp_path / "report.xlsx"
    excel_file.write_bytes(b"")
    config_file = tmp_path / "excel_config.json"

    with (
        patch.object(rule, "_IComparisonRule__resolve_config_path", return_value=config_file),
        patch.object(rule, "_IComparisonRule__resolve_sheet_name", return_value=None),
    ):
        result = list(rule.load_baseline(excel_file))

    assert result == []


def test_load_baseline_unknown_entity_no_model_class_returns_empty(tmp_path: Path) -> None:
    """load_baseline returns [] and warns when target_entity has no mapped model class."""

    class UnknownEntityRule(IComparisonRule):
        """Comparison rule targeting an unregistered entity type."""

        @property
        def severity(self) -> SeverityType:
            return SeverityType.INFO

        @property
        def target_entity(self) -> str:
            return "unknown_entity"

        @property
        def name(self) -> str:
            return "test-rule"

        @property
        def description(self) -> str:
            return "test"

        def evaluate(self, old_entries, new_entries):  # type: ignore[override]
            return []

    rule = UnknownEntityRule()
    excel_file = tmp_path / "report.xlsx"
    excel_file.write_bytes(b"")
    config_file = tmp_path / "excel_config.json"

    with (
        patch.object(rule, "_IComparisonRule__resolve_config_path", return_value=config_file),
        patch.object(rule, "_IComparisonRule__resolve_sheet_name", return_value="Sheet1"),
    ):
        result = list(rule.load_baseline(excel_file))

    assert result == []


def test_load_baseline_exception_returns_empty_list(tmp_path: Path) -> None:
    """load_baseline returns [] and logs when read_workbook raises an exception."""
    rule = ConcreteComparisonRule()
    excel_file = tmp_path / "report.xlsx"
    excel_file.write_bytes(b"")
    config_file = tmp_path / "excel_config.json"

    with (
        patch.object(rule, "_IComparisonRule__resolve_config_path", return_value=config_file),
        patch.object(rule, "_IComparisonRule__resolve_sheet_name", return_value="Users"),
        patch(
            "assets_guardian.core.domain.models.rules.comparison.read_workbook",
            side_effect=Exception("Excel read error"),
        ),
    ):
        result = list(rule.load_baseline(excel_file))

    assert result == []


# ---------------------------------------------------------------------------
# IComparisonRule.__resolve_config_path(), private method
# ---------------------------------------------------------------------------


def test_resolve_config_path_no_module_file_returns_none() -> None:
    """__resolve_config_path returns None when the module has no __file__ attribute."""
    rule = ConcreteComparisonRule()
    module_name = rule.__class__.__module__

    fake_module = MagicMock()
    fake_module.__file__ = None

    with patch.dict(sys.modules, {module_name: fake_module}):
        result = rule._IComparisonRule__resolve_config_path()  # type: ignore[attr-defined]

    assert result is None


def test_resolve_config_path_missing_config_json_returns_none(tmp_path: Path) -> None:
    """__resolve_config_path returns None when excel_config.json doesn't exist beside the module."""
    rule = ConcreteComparisonRule()
    module_name = rule.__class__.__module__

    fake_module = MagicMock()
    # Point to a directory that has no excel_config.json
    fake_module.__file__ = str(tmp_path / "rules.py")

    with patch.dict(sys.modules, {module_name: fake_module}):
        result = rule._IComparisonRule__resolve_config_path()  # type: ignore[attr-defined]

    assert result is None


def test_resolve_config_path_returns_path_when_config_exists(tmp_path: Path) -> None:
    """__resolve_config_path returns the Path when excel_config.json exists beside the module."""
    rule = ConcreteComparisonRule()
    module_name = rule.__class__.__module__

    config_file = tmp_path / "excel_config.json"
    config_file.write_text("{}")

    fake_module = MagicMock()
    fake_module.__file__ = str(tmp_path / "rules.py")

    with patch.dict(sys.modules, {module_name: fake_module}):
        result = rule._IComparisonRule__resolve_config_path()  # type: ignore[attr-defined]

    assert result == config_file


# ---------------------------------------------------------------------------
# IComparisonRule.__resolve_sheet_name(), private method
# ---------------------------------------------------------------------------


def test_resolve_sheet_name_no_matching_sheet_returns_none(tmp_path: Path) -> None:
    """__resolve_sheet_name returns None when no sheet matches the entity's data source."""
    rule = ConcreteComparisonRule()  # target_entity = "users" -> data_source = "identities"
    config_file = tmp_path / "excel_config.json"
    # Only has a sheet for "assets", not "identities"
    config_file.write_text('{"Sheet1": {"data_source": "assets"}}')

    result = rule._IComparisonRule__resolve_sheet_name(config_file)  # type: ignore[attr-defined]

    assert result is None


def test_resolve_sheet_name_matching_sheet_returned(tmp_path: Path) -> None:
    """__resolve_sheet_name returns the sheet name when a data_source match is found."""
    rule = ConcreteComparisonRule()  # target_entity = "users" -> data_source = "identities"
    config_file = tmp_path / "excel_config.json"
    config_file.write_text('{"GitLab Users": {"data_source": "identities"}}')

    result = rule._IComparisonRule__resolve_sheet_name(config_file)  # type: ignore[attr-defined]

    assert result == "GitLab Users"


def test_resolve_sheet_name_invalid_json_raises_value_error(tmp_path: Path) -> None:
    """__resolve_sheet_name raises ValueError when the config file contains invalid JSON."""
    rule = ConcreteComparisonRule()
    bad_file = tmp_path / "excel_config.json"
    bad_file.write_text("{ not valid json }")

    with pytest.raises(ValueError, match="Error resolving"):
        rule._IComparisonRule__resolve_sheet_name(bad_file)  # type: ignore[attr-defined]


def test_load_baseline_success(tmp_path: Path) -> None:
    """load_baseline successfully reads workbook and parses it."""
    rule = ConcreteComparisonRule()
    excel_file = tmp_path / "report.xlsx"
    excel_file.write_bytes(b"")
    config_file = tmp_path / "excel_config.json"
    with (
        patch.object(rule, "_IComparisonRule__resolve_config_path", return_value=config_file),
        patch.object(rule, "_IComparisonRule__resolve_sheet_name", return_value="Users"),
        patch("assets_guardian.core.domain.models.rules.comparison.read_workbook", return_value={}),
        patch(
            "assets_guardian.core.domain.models.rules.comparison.parse_workbook_data",
            return_value=[1, 2, 3],
        ) as mock_parser,
    ):
        result = list(rule.load_baseline(excel_file))
    assert result == [1, 2, 3]
    mock_parser.assert_called_once()


def test_load_baseline_sheet_name_renaming_starts_with_prefix(tmp_path: Path) -> None:
    """load_baseline correctly renames the sheet using parentheses when it starts with prefix."""
    rule = ConcreteComparisonRule()
    excel_file = tmp_path / "report.xlsx"
    excel_file.write_bytes(b"")
    config_file = tmp_path / "excel_config.json"

    with (
        patch.object(rule, "_IComparisonRule__resolve_config_path", return_value=config_file),
        patch.object(rule, "_IComparisonRule__resolve_sheet_name", return_value="Unknown Users"),
        patch(
            "assets_guardian.core.domain.models.rules.comparison.read_workbook", return_value={}
        ) as mock_read,
        patch(
            "assets_guardian.core.domain.models.rules.comparison.parse_workbook_data",
            return_value=[1, 2, 3],
        ),
    ):
        list(rule.load_baseline(excel_file))
        mock_read.assert_called_once_with(excel_file, sheet_names=["Unknown (default) Users"])
