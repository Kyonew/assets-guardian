"""Tests for the field level type and value validation utilities."""

from dataclasses import dataclass

import pytest

from assets_guardian.core.domain.models.validator import validate_field


@dataclass
class DummyClass:
    """Mock class containing fields of various types to test validation mechanisms."""

    field1: str
    field2: int
    field3: list | None
    field4: str


def test_validate_field_optional_none() -> None:
    """Verify that validate_field permits None values when optional is True."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    # Should not raise
    validate_field(obj, "field3", list, optional=True)


def test_validate_field_type_error_single_type() -> None:
    """Verify that validate_field raises TypeError when field receives an incorrect type (single expected type)."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    # Expected type error
    with pytest.raises(TypeError, match="must be a int"):
        validate_field(obj, "field1", int)


def test_validate_field_type_error_tuple_types() -> None:
    """Verify that validate_field raises TypeError when field fails check against a tuple of allowed types."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    # Expected type error
    with pytest.raises(TypeError, match="must be a int \\| float"):
        validate_field(obj, "field1", (int, float))


def test_validate_field_value_error_empty() -> None:
    """Verify that validate_field raises ValueError if empty strings are passed when empty is set to False."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    # Empty string should raise error with empty=False (default)
    with pytest.raises(ValueError, match="must be a non-empty value"):
        validate_field(obj, "field4", str, empty=False)


def test_validate_field_empty_allowed() -> None:
    """Verify that validate_field accepts empty strings when empty parameter is True."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    # Should not raise since empty=True
    validate_field(obj, "field4", str, empty=True)


def test_validate_field_int_zero_allowed() -> None:
    """Verify that integer value 0 is not falsely flagged as empty."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    # 0 is falsy, but it's an int, so it shouldn't raise empty ValueError
    validate_field(obj, "field2", int, empty=False)


def test_validate_field_none_not_optional() -> None:
    """Verify that validate_field raises TypeError when a required (non-optional) field is None."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    with pytest.raises(TypeError, match="must be a list"):
        validate_field(obj, "field3", list, optional=False)


def test_validate_field_float_zero_allowed() -> None:
    """Verify that float value 0.0 is not falsely flagged as empty."""

    @dataclass
    class DummyWithFloat:
        field_float: float

    obj = DummyWithFloat(field_float=0.0)
    validate_field(obj, "field_float", float, empty=False)


def test_validate_field_empty_list_raises() -> None:
    """Verify that an empty list raises ValueError when empty=False."""

    @dataclass
    class DummyWithList:
        items: list

    obj = DummyWithList(items=[])
    with pytest.raises(ValueError, match="must be a non-empty value"):
        validate_field(obj, "items", list, empty=False)


def test_validate_field_valid_value() -> None:
    """Verify that correct field types successfully validate under standard options."""
    obj = DummyClass(field1="hello", field2=42, field3=["x"], field4="ok")
    validate_field(obj, "field1", str)  # Should not raise


def test_validate_field_tuple_types_valid() -> None:
    """Verify that values matching one of the options in a tuple of types successfully validate."""
    obj = DummyClass(field1="test", field2=42, field3=None, field4="ok")
    validate_field(obj, "field2", (int, float))  # Should not raise


def test_validate_field_optional_wrong_type_mentions_or_none() -> None:
    """Verify that TypeError message mentions 'or None' when validating optional fields."""
    obj = DummyClass(field1="test", field2=0, field3=None, field4="")
    with pytest.raises(TypeError, match="or None"):
        validate_field(obj, "field1", int, optional=True)


def test_validate_field_bool_treated_as_int() -> None:
    """Verify that booleans are correctly evaluated as independent from integer assertions."""

    @dataclass
    class DummyWithBool:
        flag: bool

    obj = DummyWithBool(flag=False)
    # False is falsy, but is an instance of bool, so it should validate successfully
    validate_field(obj, "flag", bool, empty=False)


def test_validate_field_empty_dict_raises() -> None:
    """Verify that an empty dictionary raises ValueError when empty=False."""

    @dataclass
    class DummyWithDict:
        data: dict

    obj = DummyWithDict(data={})
    with pytest.raises(ValueError, match="must be a non-empty value"):
        validate_field(obj, "data", dict, empty=False)
