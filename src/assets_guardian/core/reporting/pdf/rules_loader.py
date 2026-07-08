"""PDF rules and styles loader for Assets Guardian."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_PDF_RULES: dict[str, Any] = {
    "colors": {
        "CRITICAL": {"r": 255, "g": 0, "b": 0},  # Red
        "DANGER": {"r": 255, "g": 69, "b": 0},  # Red-Orange
        "WARNING": {"r": 255, "g": 165, "b": 0},  # Orange
        "INFO": {"r": 0, "g": 122, "b": 255},  # Blue
        "header_bg": {"r": 208, "g": 208, "b": 208},  # Light grey
        "text": {"r": 0, "g": 0, "b": 0},  # Black
    },
    "fonts": {
        "title": {"family": "helvetica", "style": "B", "size": 16},
        "subtitle": {"family": "helvetica", "style": "B", "size": 14},
        "heading": {"family": "helvetica", "style": "B", "size": 12},
        "body": {"family": "helvetica", "style": "", "size": 10},
    },
}


def load_rules(rules_file_path: str | Path | None = None) -> dict[str, Any]:
    """Loads PDF style rules from a JSON file.

    Returns the default styles if the file does not exist.
    """
    rules = DEFAULT_PDF_RULES.copy()

    if not rules_file_path:
        return rules

    path = Path(rules_file_path)
    if not path.is_file():
        logger.warning("PDF rules file not found: %s. Using defaults.", rules_file_path)
        return rules

    try:
        with path.open(encoding="utf-8") as file:
            custom_rules = json.load(file)
            if isinstance(custom_rules, dict):
                # Recursively update defaults with custom rules
                for key, value in custom_rules.items():
                    if key in rules and isinstance(rules[key], dict) and isinstance(value, dict):
                        rules[key].update(value)
                    else:
                        rules[key] = value
    except Exception:
        logger.exception("Error loading PDF rules from %s", rules_file_path)

    return rules
