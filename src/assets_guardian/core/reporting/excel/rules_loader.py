"""Excel rules loader for Assets Guardian."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_rules(rules_file_path: str | Path) -> dict[str, Any]:
    """Loads validation rules from a JSON file."""

    if not Path(rules_file_path).is_file():
        logger.warning("Rules file not found: %s", rules_file_path)
        return {}

    with Path(rules_file_path).open(encoding="utf-8") as file:
        data = json.load(file)
        return data if isinstance(data, dict) else {}
