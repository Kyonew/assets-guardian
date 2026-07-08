"""Tests for the Finding and Report models representing security audit results and compliance summaries."""

from datetime import UTC, datetime

import pytest

from assets_guardian.core.domain.models.finding import Finding, RuleCategory, SeverityType
from assets_guardian.core.domain.models.report import Report


@pytest.fixture
def valid_finding_data() -> dict:
    """Provide a dictionary of valid initialization parameters for Finding model."""
    return {
        "rule_id": "RULE-001",
        "severity": SeverityType.DANGER,
        "rule_category": RuleCategory.COMPLIANCE,
        "title": "Security Issue",
        "description": "A serious security issue was found.",
        "source": "gitlab",
        "instance_id": "gitlab.com",
        "entities_impacted": ["user@example.com"],
        "timestamp": datetime.now(tz=UTC),
    }


def test_finding_creation_success(valid_finding_data) -> None:
    """Verify that a Finding instance is initialized successfully when valid inputs are provided."""
    finding = Finding(**valid_finding_data)
    assert finding.rule_id == "RULE-001"
    assert finding.severity == SeverityType.DANGER
    assert finding.rule_category == RuleCategory.COMPLIANCE
    assert finding.title == "Security Issue"
    assert finding.description == "A serious security issue was found."
    assert finding.source == "gitlab"
    assert finding.instance_id == "gitlab.com"
    assert finding.entities_impacted == ["user@example.com"]
    assert isinstance(finding.timestamp, datetime)


def test_finding_missing_arguments() -> None:
    """Verify that initializing Finding without mandatory arguments raises TypeError."""
    with pytest.raises(TypeError):
        # Missing all required keyword-only arguments
        Finding()  # type: ignore


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("rule_id", 123),
        ("rule_category", "invalid_category"),
        ("severity", "VERY_HIGH"),
        ("title", None),
        ("description", []),
        ("source", 1.0),
        ("instance_id", {}),
        ("entities_impacted", "not-a-list"),
        ("timestamp", "2024-01-01"),
    ],
)
def test_finding_type_validation(valid_finding_data, field, invalid_value) -> None:
    """Verify that Finding raises TypeError when fields receive invalid types."""
    data = valid_finding_data.copy()
    data[field] = invalid_value
    with pytest.raises(TypeError):
        Finding(**data)


def test_finding_immutability(valid_finding_data) -> None:
    """Verify that Finding fields are frozen and cannot be modified after instantiation."""
    finding = Finding(**valid_finding_data)
    with pytest.raises(AttributeError):
        finding.rule_id = "NEW-RULE"  # type: ignore


def test_finding_metadata_valid(valid_finding_data) -> None:
    """Verify that Finding metadata accepts a valid dictionary successfully."""
    finding = Finding(**valid_finding_data, metadata={"key": "value"})
    assert finding.metadata == {"key": "value"}


def test_finding_metadata_none_by_default(valid_finding_data) -> None:
    """Verify that Finding metadata defaults to None when omitted."""
    finding = Finding(**valid_finding_data)
    assert finding.metadata is None


def test_finding_metadata_invalid_type(valid_finding_data) -> None:
    """Verify that Finding raises TypeError if metadata parameter is not a dictionary."""
    data = {**valid_finding_data, "metadata": "not-a-dict"}
    with pytest.raises(TypeError):
        Finding(**data)


def test_finding_empty_entities_impacted(valid_finding_data) -> None:
    """Verify that Finding raises ValueError if entities_impacted is provided as an empty list."""
    with pytest.raises(ValueError, match="must be a non-empty value"):
        Finding(**{**valid_finding_data, "entities_impacted": []})


@pytest.mark.parametrize("severity", list(SeverityType))
def test_finding_all_severities(valid_finding_data, severity) -> None:
    """Verify that Finding successfully maps all SeverityType enum values."""
    finding = Finding(**{**valid_finding_data, "severity": severity})
    assert finding.severity == severity


@pytest.mark.parametrize("category", list(RuleCategory))
def test_finding_all_rule_categories(valid_finding_data, category) -> None:
    """Verify that Finding successfully maps all RuleCategory enum values."""
    finding = Finding(**{**valid_finding_data, "rule_category": category})
    assert finding.rule_category == category


def test_finding_report_initialization() -> None:
    """Verify that Report initializes with zero elements and zero count for all severities."""
    report = Report()
    assert report.total_count == 0
    assert len(report) == 0
    for severity in SeverityType:
        assert report.get_count_by_severity(severity) == 0


def test_finding_report_add_finding(valid_finding_data) -> None:
    """Verify that Report correctly adds a single Finding, updating length and severity counters."""
    report = Report()
    finding = Finding(**valid_finding_data)
    report.add_finding(finding)

    assert report.total_count == 1
    assert len(report) == 1
    assert report.get_count_by_severity(finding.severity) == 1

    # Check iteration
    findings = list(report)
    assert len(findings) == 1
    assert findings[0] == finding


def test_finding_report_extend(valid_finding_data) -> None:
    """Verify that Report correctly extends findings with a list of Findings, updating severities count."""
    report = Report()
    f1 = Finding(**{**valid_finding_data, "rule_id": "R1", "severity": SeverityType.CRITICAL})
    f2 = Finding(**{**valid_finding_data, "rule_id": "R2", "severity": SeverityType.INFO})

    report.extend([f1, f2])

    assert report.total_count == 2
    assert report.get_count_by_severity(SeverityType.CRITICAL) == 1
    assert report.get_count_by_severity(SeverityType.INFO) == 1
    assert report.get_count_by_severity(SeverityType.DANGER) == 0


def test_finding_report_get_count_by_severity_missing() -> None:
    """Verify that get_count_by_severity returns 0 when no findings of that severity exist in the Report."""
    report = Report()
    assert report.get_count_by_severity(SeverityType.WARNING) == 0


def test_finding_report_streaming_mode(valid_finding_data) -> None:
    """Verify that Report correctly acts as an iterator wrapper when initialized with pre-existing findings."""
    f1 = Finding(**{**valid_finding_data, "rule_id": "R1"})
    # Report initialized with an iterable (simulating streaming)
    report = Report(findings=[f1])

    assert report.total_count == 1
    # Check iteration uses the external iterable
    findings = list(report)
    assert len(findings) == 1
    assert findings[0] == f1
