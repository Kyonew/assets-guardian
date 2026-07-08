import json
import logging
import sys
from abc import abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.finding import Finding, RuleCategory
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.models.rules.rule import IRule
from assets_guardian.core.reporting.excel.generic_parser import parse_workbook_data
from assets_guardian.core.reporting.excel.reader import read_workbook


class IComparisonRule(IRule):
    @property
    def rule_category(self) -> RuleCategory:
        """Rule category: COMPARISON (comparison rules)."""
        return RuleCategory.COMPARISON

    @abstractmethod
    def evaluate(self, old_entries: Iterable[Any], new_entries: Iterable[Any]) -> Iterable[Finding]:  # type: ignore
        """Compares two lists of entries (users, groups, projects, accesses).

        Args:
            old_entries: Data extracted from the existing Excel referential.
            new_entries: Freshly collected data.

        Returns:
            Iterable[Finding]: List of detected discrepancies (additions, deletions, updates).
        """
        raise NotImplementedError

    def load_baseline(self, excel_path: Path | None = None) -> Iterable[Any]:
        """Loads the previous baseline for this rule from the specified or configured Excel file."""
        if not excel_path:
            return []

        logger = logging.getLogger(__name__)

        try:
            config_path = self.__resolve_config_path()
            if not config_path:
                logger.warning(
                    "No excel_config.json file found for rule %s",
                    getattr(self, "rule_id", "unknown"),
                )
                return []

            # Extract source (plugin name)
            module_parts = self.__class__.__module__.split(".")
            source = (
                module_parts[2].lower()
                if len(module_parts) > 2 and module_parts[1] == "plugins"
                else "unknown"
            )

            sheet_name = self.__resolve_sheet_name(config_path)
            if sheet_name:
                instance_id = getattr(self, "instance_id", "default")
                # Apply the same naming convention as the builder to read the correct sheet
                prefix = source.capitalize()
                if sheet_name.startswith(prefix):
                    sheet_name = sheet_name.replace(prefix, f"{prefix} ({instance_id})", 1)
                else:
                    sheet_name = f"{sheet_name} ({instance_id})"
            if not sheet_name:
                logger.warning(
                    "No sheet configured for rule %s in %s",
                    getattr(self, "rule_id", "unknown"),
                    config_path,
                )
                return []

            model_class = self.__resolve_model_class()
            if not model_class:
                logger.warning("No known model class for entity '%s'", self.target_entity)
                return []

            # Generic loading and parsing
            workbook_data = read_workbook(excel_path, sheet_names=[sheet_name])
            return parse_workbook_data(
                workbook_data=workbook_data,
                sheet_name=sheet_name,
                model_class=model_class,
                rules_file_path=config_path,
                source=source,
            )

        except Exception:
            logger.exception(
                "Error during baseline generic loading for rule %s",
                getattr(self, "rule_id", "unknown"),
            )
            return []

    def __resolve_config_path(self) -> Path | None:
        """Resolves the path to the plugin's excel_config.json file.

        Returns:
            Path | None: Path to the excel_config.json file or None if it doesn't exist.
        """
        module_file = sys.modules[self.__class__.__module__].__file__
        if not module_file:
            return None
        config_path = Path(module_file).parent / "excel_config.json"
        return config_path if config_path.is_file() else None

    def __resolve_sheet_name(self, config_path: Path) -> str | None:
        """Finds the sheet name associated with the target entity in the configuration.

        Args:
            config_path: Path to the excel_config.json file.

        Returns:
            str | None: Target entity sheet name, or None if not configured.

        Raises:
            ValueError: If an error occurs while reading or analyzing the JSON.
        """
        try:
            with config_path.open(encoding="utf-8") as f:
                config_data = json.load(f)

            entity_to_datasource = {
                "users": "identities",
                "assets": "assets",
                "accesses": "accesses",
            }
            target_ds = entity_to_datasource.get(self.target_entity, self.target_entity)

            for sheet, sheet_cfg in config_data.items():
                if sheet_cfg.get("data_source") == target_ds:
                    return str(sheet)
        except Exception as e:
            raise ValueError("Error resolving the sheet name") from e
        return None

    def __resolve_model_class(self) -> type | None:
        """Returns the domain model class associated with the target entity.

        Returns:
            type | None: Model class (Identity, Asset, Access) or None if unrecognized.
        """
        entity_to_model = {
            "users": Identity,
            "assets": Asset,
            "accesses": Access,
        }
        return entity_to_model.get(self.target_entity)
