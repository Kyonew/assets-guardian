from collections.abc import Iterable, Iterator

from assets_guardian.core.domain.models.finding import Finding, SeverityType


class Report:
    """Container for audit findings, allowing tracking of metrics.

    Can operate either in "memory" mode (classic list) or in
    "streaming" mode (external iterable such as a cache) to prevent RAM saturation.
    """

    def __init__(self, findings: Iterable[Finding] | None = None) -> None:
        """Initializes the report, possibly in streaming mode.

        Args:
            findings: An optional iterable of findings (e.g., from cache).
                If present, the report switches to streaming mode.
        """
        self._findings_list: list[Finding] = []
        self._external_iterable: Iterable[Finding] | None = findings
        self._counts_by_severity: dict[SeverityType, int] = dict.fromkeys(SeverityType, 0)

        if findings:
            self.extend(findings)

    def add_finding(self, finding: Finding) -> None:
        """Adds a finding to the report and updates severity counters.

        Args:
            finding: The detected anomaly to integrate.
        """
        # We only store in the internal list if we do not have an external iterable
        # or if we want to force keeping in memory.
        if self._external_iterable is None:
            self._findings_list.append(finding)

        self._counts_by_severity[finding.severity] += 1

    def extend(self, findings: Iterable[Finding]) -> None:
        """Adds multiple findings to the report in bulk.

        Args:
            findings: An iterable of findings to process.
        """
        for finding in findings:
            self.add_finding(finding)

    @property
    def total_count(self) -> int:
        """Total count of detected findings."""
        return sum(self._counts_by_severity.values())

    def get_count_by_severity(self, severity: SeverityType) -> int:
        """Returns the count of findings for a given severity."""
        return self._counts_by_severity.get(severity, 0)

    def __iter__(self) -> Iterator[Finding]:
        """Allows iterating over findings.

        Prioritizes the external iterable (streaming) if present, otherwise the internal list.
        """
        if self._external_iterable is not None:
            return iter(self._external_iterable)
        return iter(self._findings_list)

    def __len__(self) -> int:
        """Enables the use of len(report)."""
        return self.total_count
