from typing import Any

from assets_guardian.core.config.loader import browse_dict

from .app_config import CORE_KEYS


def validate_config(raw_config: dict[str, Any], template: dict[str, Any], prefix: str = "") -> None:
    """Recursively verifies that the raw configuration matches the template.

    Args:
        raw_config: Dictionary containing raw configuration data.
        template: Dictionary containing the configuration template.
        prefix: Prefix for nested keys.

    Raises:
        TypeError: If the raw configuration value does not match the expected dict type.
        KeyError: If a mandatory configuration key is missing.
    """
    for key, template_value in template.items():
        # Do not check if it is an integration
        if not prefix and key not in CORE_KEYS:
            continue

        full_key = f"{prefix}:{key}" if prefix else key

        if isinstance(template_value, dict):
            # Check if the key exists in raw_config
            # Use browse_dict to get the raw dictionary value without string conversions
            current = browse_dict(raw_config, full_key)
            if current is not None and not isinstance(current, dict):
                raise TypeError(f"Configuration key '{full_key}' must be a dictionary")
            # Recursively validate the sub-template
            validate_config(raw_config, template_value, full_key)
        else:
            # AppConfig will decide if the key is required or has a default value.
            pass
