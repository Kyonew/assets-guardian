"""Tests for core/reporting/excel/writer.py covering the sheet name generation and preservation."""

from typing import Any
from unittest.mock import MagicMock, patch

from assets_guardian.core.domain.ports.sheet_builders import ISheetBuilder
from assets_guardian.core.reporting.excel.writer import ExcelWriter


class DummySheetBuilder(ISheetBuilder):
    """A minimal implementation of ISheetBuilder for testing."""

    def __init__(
        self, source_name: str, instance_id: str = "", sheet_names: list[str] | None = None
    ):
        self._source_name = source_name
        self._instance_id = instance_id
        self._sheet_names = sheet_names or []

    @property
    def source_name(self) -> str:
        return self._source_name

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def sheet_names(self) -> list[str]:
        return self._sheet_names

    def build(self, worksheet, data, preserved, rules) -> None:
        pass

    @property
    def preserved_columns(self) -> dict[str, dict[str, list[str]]]:
        return {}

    def get_rules(self) -> dict[str, list[dict[str, Any]]]:
        return {}


def test_excel_writer_process_builder_adds_matrix_names():
    """Verify that __process_builder correctly capitalizes source name and Matrix word."""
    writer = ExcelWriter()
    workbook = MagicMock()

    # 1. Builder with instance_id
    builder_with_instance = DummySheetBuilder(source_name="gitlab", instance_id="prod")

    with patch.object(writer, "_ExcelWriter__build_sheet") as mock_build:
        writer._ExcelWriter__process_builder(
            workbook=workbook,
            builder=builder_with_instance,
            data={},
            existing_data={},
            rules={},
        )

        # Should call __build_sheet with capitalized Gitlab and Matrix
        mock_build.assert_called_once_with(
            workbook,
            builder_with_instance,
            "Gitlab (prod) Matrix",
            {},
            {},
            {},
        )

    # 2. Builder without instance_id
    builder_no_instance = DummySheetBuilder(source_name="gitlab")

    with patch.object(writer, "_ExcelWriter__build_sheet") as mock_build:
        writer._ExcelWriter__process_builder(
            workbook=workbook,
            builder=builder_no_instance,
            data={},
            existing_data={},
            rules={},
        )

        # Should call __build_sheet with capitalized Gitlab and Matrix
        mock_build.assert_called_once_with(
            workbook,
            builder_no_instance,
            "Gitlab Matrix",
            {},
            {},
            {},
        )


def test_excel_writer_process_builder_preserves_case_insensitively():
    """Verify that __process_builder checks existing sheets case-insensitively and copies them."""
    writer = ExcelWriter()
    workbook = MagicMock()

    builder = DummySheetBuilder(source_name="gitlab", instance_id="prod")
    existing_data = {
        "gitlab (prod) matrix": {
            "header": {1: {"title": "Profile"}},
            "content": [],
        }
    }

    with (
        patch.object(writer, "_ExcelWriter__copy_sheet") as mock_copy,
        patch.object(writer, "_ExcelWriter__build_sheet") as mock_build,
    ):
        writer._ExcelWriter__process_builder(
            workbook=workbook,
            builder=builder,
            data={},
            existing_data=existing_data,
            rules={},
        )

        # Should identify "gitlab (prod) matrix" matching "Gitlab (prod) Matrix"
        # and copy it using the new capitalized sheet name.
        mock_copy.assert_called_once_with(
            workbook, "Gitlab (prod) Matrix", existing_data["gitlab (prod) matrix"]
        )
        mock_build.assert_not_called()
