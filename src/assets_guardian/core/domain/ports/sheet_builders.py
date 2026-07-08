from abc import ABC, abstractmethod
from typing import Any


class ISheetBuilder(ABC):
    """Port: Excel sheet builder (Plugin).

    Contract for plugins wishing to add specific sheets
    to the Excel referential.
    """

    # Injected by the registry upon registration
    source_name: str = ""

    @property
    @abstractmethod
    def sheet_names(self) -> list[str]:
        """List of Excel sheet names managed by this builder."""
        raise NotImplementedError

    @property
    @abstractmethod
    def preserved_columns(self) -> dict[str, dict[str, list[str]]]:
        """Defines the columns to preserve per sheet.

        Example::

            {
                'Sheet1': {'primary_keys': ['ID'], 'columns': ['Comments']},
                'Sheet2': {'primary_keys': ['UUID'], 'columns': ['Account Type']}
            }
        """
        raise NotImplementedError

    @abstractmethod
    def get_rules(self) -> dict[str, Any]:
        """Returns plugin-specific Excel formatting rules."""
        raise NotImplementedError

    @abstractmethod
    def build(
        self,
        worksheet: Any,
        data: Any,
        preserved: Any,
        rules: Any,
    ) -> None:
        """Builds the Excel sheet for this plugin.

        Args:
            worksheet: The Excel sheet (ExcelWorksheet).
            data: Dictionary of collection results (source, instance) -> CollectorResult.
            preserved: Manual data extracted from the existing sheet for preservation.
            rules: Formatting and validation rules.
        """
        raise NotImplementedError
