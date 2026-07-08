import dataclasses
import logging
import typing
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Any

from assets_guardian.core.domain.models.identity import IdentityType
from assets_guardian.core.reporting.excel.rules_loader import load_rules
from assets_guardian.utils.dates import parse_datetime

logger = logging.getLogger(__name__)


def __extract_sheet_columns_configuration(
    rules_file_path: str | Path, sheet_name: str
) -> list[dict[str, Any]] | Any:
    """Retrieves the column definitions for a sheet from the rules file.

    Args:
        rules_file_path: Path to the JSON configuration file.
        sheet_name: Name of the worksheet.

    Returns:
        list[dict[str, Any]]: List of column configurations for the sheet.
    """
    all_rules = load_rules(rules_file_path)
    sheet_config = all_rules.get(sheet_name)
    if not sheet_config:
        for orig_key in all_rules:
            if " (" in sheet_name and ")" in sheet_name:
                parts = sheet_name.split(" (")
                prefix = parts[0]
                if ") " in parts[1]:
                    rest = parts[1].split(") ", 1)[1]
                    candidate = f"{prefix} {rest}"
                else:
                    candidate = prefix
                if candidate == orig_key:
                    sheet_config = all_rules[orig_key]
                    break

    if not sheet_config:
        return []
    if isinstance(sheet_config, list):
        return sheet_config
    return sheet_config.get("columns", [])


def __apply_config_mapping(cell_value: Any, mapping: dict[str, Any] | None) -> Any:
    """Applies the mapping dictionary from Excel configuration if defined.

    Args:
        cell_value: Raw cell value read from Excel.
        mapping: Configured mappings for this column.

    Returns:
        Any: Mapped value if matches found, otherwise original value.
    """
    if not mapping or cell_value is None:
        return cell_value
    cell_value_string = str(cell_value).strip().lower()
    for mapping_key, mapping_value in mapping.items():
        if str(mapping_key).strip().lower() == cell_value_string:
            return mapping_value
    return cell_value


def __resolve_field_type(target_field_type: Any) -> Any:
    """Resolves the field type by extracting arguments from Unions.

    Args:
        target_field_type: Type hint associated with the model field.

    Returns:
        Any: Extracted base type, or Any if undetermined.
    """
    type_args = typing.get_args(target_field_type)
    if not type_args:
        return target_field_type
    types_list = [t for t in type_args if t is not type(None)]
    return types_list[0] if types_list else Any


def __cast_to_field_type(cell_value: Any, target_field_type: Any) -> Any:
    """Strictly casts the value to the type expected by the model.

    Args:
        cell_value: Value from the cell or mapping.
        target_field_type: Targeted type defined by the model.

    Returns:
        Any: Casted value (datetime, Enum, IP, or bool) or the raw value.
    """
    if cell_value is None:
        return None

    target_type = __resolve_field_type(target_field_type)

    if target_type is datetime:
        return parse_datetime(cell_value)

    is_enum = isinstance(target_type, type) and issubclass(target_type, Enum)
    is_ip = target_type in (IPv4Address, IPv6Address)

    if is_enum or is_ip:
        try:
            return target_type(cell_value)
        except ValueError:
            return cell_value

    if target_type is bool and not isinstance(cell_value, bool):
        return bool(cell_value)

    return cell_value


def __parse_single_excel_row(
    row_values: list[Any],
    columns_configuration: list[dict[str, Any]],
    header_indices: dict[str, int],
    supported_model_fields: set[str],
    type_hints: dict[str, Any],
    source: str,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    """Parses a single Excel row into model arguments and metadata.

    Args:
        row_values: List of raw values from the Excel row.
        columns_configuration: Column configurations for the sheet.
        header_indices: Dictionary mapping lowercase column titles to their indices.
        supported_model_fields: Set of field names recognized by the dataclass.
        type_hints: Type hints declared by the destination model.
        source: Collection source name.

    Returns:
        tuple[dict[str, Any], dict[str, Any], bool]: A tuple containing:
            - The arguments for the model to instantiate.
            - Metadata not supported as direct attributes.
            - A boolean indicating if a valid primary key value was read.
    """
    model_arguments = {}
    metadata_values = {}
    has_primary_key_value = False

    if "source" in supported_model_fields:
        model_arguments["source"] = source

    for column in columns_configuration:
        if column.get("is_preserved"):
            continue

        column_name = column.get("column_name", "")
        field_name = column.get("field", column_name)
        if not field_name:
            continue

        col_index = header_indices.get(column_name.strip().lower())
        if col_index is None or col_index >= len(row_values):
            continue

        cell_value = row_values[col_index]

        if column.get("is_primary_key") and cell_value is not None:
            has_primary_key_value = True

        cell_value = __apply_config_mapping(cell_value, column.get("mapping"))
        cell_value = __cast_to_field_type(cell_value, type_hints.get(field_name, Any))

        if field_name in supported_model_fields:
            model_arguments[field_name] = cell_value
        else:
            metadata_values[field_name] = cell_value

    return model_arguments, metadata_values, has_primary_key_value


def __get_sheet_data(workbook_data: dict[str, Any], sheet_name: str) -> dict[str, Any] | Any | None:
    """Retrieves Excel sheet data after validation.

    Args:
        workbook_data: Raw content of the Excel workbook.
        sheet_name: Name of the sheet to extract.

    Returns:
        dict[str, Any] | None: Raw sheet data or None if absent/incomplete.
    """
    if sheet_name not in workbook_data:
        logger.warning("Sheet '%s' is absent from the Excel workbook data.", sheet_name)
        return None

    sheet_data = workbook_data[sheet_name]
    if not sheet_data.get("header") or not sheet_data.get("content"):
        logger.warning("Sheet '%s' does not contain any data.", sheet_name)
        return None

    return sheet_data


def __instantiate_model(
    model_class: type,
    model_arguments: dict[str, Any],
    metadata_values: dict[str, Any],
    supported_model_fields: set[str],
) -> Any | None:
    """Instantiates the domain model with optional supplementary metadata.

    Args:
        model_class: The model class to instantiate (e.g., Identity).
        model_arguments: Constructor arguments for the model.
        metadata_values: Dictionary of out-of-model metadata to inject.
        supported_model_fields: Set of fields supported by the model.

    Returns:
        Any | None: The created domain model instance, or None if failed.
    """
    if "metadata" in supported_model_fields and metadata_values:
        existing_metadata = model_arguments.get("metadata") or {}
        existing_metadata.update(metadata_values)
        model_arguments["metadata"] = existing_metadata

    if model_class.__name__ == "Identity" and "identity_type" not in model_arguments:
        model_arguments["identity_type"] = IdentityType.GENERIC

    try:
        return model_class(**model_arguments)
    except Exception:
        logger.exception("Failed to instantiate model %s.", model_class.__name__)
        return None


def parse_workbook_data(
    workbook_data: dict[str, Any],
    sheet_name: str,
    model_class: type,
    rules_file_path: str | Path,
    source: str = "unknown",
) -> list[Any]:
    """Parses an Excel sheet to instantiate domain models.

    Args:
        workbook_data: Raw workbook data read by read_workbook.
        sheet_name: Name of the Excel sheet to parse.
        model_class: The domain model class to instantiate (e.g., Identity).
        rules_file_path: Path to the excel_config.json containing the rules.
        source: Technical name of the source (e.g., "gitlab").

    Returns:
        list[Any]: List of reconstructed domain model instances.
    """
    sheet_data = __get_sheet_data(workbook_data, sheet_name)
    if not sheet_data:
        return []

    columns_configuration = __extract_sheet_columns_configuration(rules_file_path, sheet_name)
    if not columns_configuration:
        logger.warning("No configuration found for sheet '%s' in the rules.", sheet_name)
        return []

    header_indices = {
        info["title"].strip().lower(): col_index - 1
        for col_index, info in sheet_data["header"].items()
    }

    supported_model_fields = {field.name for field in dataclasses.fields(model_class)}
    type_hints = typing.get_type_hints(model_class)
    instantiated_models = []

    has_defined_primary_key = any(col.get("is_primary_key") for col in columns_configuration)

    for row_values in sheet_data["content"]:
        model_arguments, metadata_values, has_pk = __parse_single_excel_row(
            row_values,
            columns_configuration,
            header_indices,
            supported_model_fields,
            type_hints,
            source,
        )

        if has_defined_primary_key and not has_pk:
            continue

        model_instance = __instantiate_model(
            model_class, model_arguments, metadata_values, supported_model_fields
        )
        if model_instance:
            instantiated_models.append(model_instance)

    return instantiated_models
