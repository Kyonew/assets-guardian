def validate_field(
    instance: object,
    field: str,
    expected_type: type | tuple[type, ...],
    *,  # The following arguments are keyword-only parameters for clarity
    optional: bool = False,
    empty: bool = False,
) -> None:
    """Validates the type and non-emptiness of a dataclass field.

    The validation is performed in three ordered steps:
        1. If optional is True and the value is None, the field is valid.
        2. If the value is not of the expected type, a TypeError is raised.
        3. If empty is False and the value is falsy (empty string, empty list, etc.),
            a ValueError is raised. Numeric types (int, float) are excluded from this check
            to allow 0 and 0.0.

    Args:
        instance: Instance of the dataclass to validate.
        field: Name of the field to check.
        expected_type: Expected type or tuple of types for the field.
        optional: If True, accepts None as a valid value. Defaults to False.
        empty: If True, allows falsy values (empty string, empty list, etc.).
            Defaults to False (strict).

    Raises:
        TypeError: If the field is not of the expected type (or None when optional is False).
        ValueError: If the field has a falsy non-numeric value and empty is False.
    """
    value = getattr(instance, field)
    # If the field is optional and the value is None, it is valid.
    if optional and value is None:
        return
    # If the value is not of the expected type, it's an error.
    if not isinstance(value, expected_type):  # isinstance natively accepts a tuple of types
        if isinstance(expected_type, tuple):
            type_names = " | ".join(t.__name__ for t in expected_type)
        else:
            type_names = expected_type.__name__
        raise TypeError(
            f"Field {field!r} must be a {type_names}"
            f"{' or None' if optional else ''}, got "
            f"{type(value).__name__}."
        )

    # If the value is falsy, empty is False, and it is not a number, it's an error.
    # We allow numbers to be 0 or 0.0 even though they are falsy.
    if not empty and not value and not isinstance(value, int | float):
        raise ValueError(f"Field {field!r} must be a non-empty value.")
