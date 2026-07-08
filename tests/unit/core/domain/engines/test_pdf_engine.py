"""Tests for core/domain/engines/pdf_engine.py."""

from unittest.mock import MagicMock, patch

from assets_guardian.core.domain.engines.pdf_engine import PdfEngine
from assets_guardian.core.domain.models.context import Context


def test_pdf_engine_generate_with_dict_data() -> None:
    """generate() extracts dict.values() when data is a dict and passes them to the writer."""
    engine = PdfEngine()
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.pdf_config.clean_path = "/pdf_config.json"
    ctx.app_config.paths.pdf.clean_path = "/output/report.pdf"

    mock_report_a = MagicMock()
    mock_report_b = MagicMock()
    data = {"source_a": mock_report_a, "source_b": mock_report_b}

    mock_writer = MagicMock()

    with (
        patch(
            "assets_guardian.core.domain.engines.pdf_engine.PDFBuilderRegistry.get_builders",
            return_value=[],
        ),
        patch(
            "assets_guardian.core.domain.engines.pdf_engine.PDFWriter",
            return_value=mock_writer,
        ) as mock_writer_cls,
    ):
        engine.generate(data, ctx)

    mock_writer_cls.assert_called_once_with(
        pdf_builders=[],
        rules_file_path="/pdf_config.json",
    )
    # The writer must have received dict.values() (the two report mocks)
    call_args = mock_writer.write.call_args
    written_reports = list(call_args[0][0])
    assert mock_report_a in written_reports
    assert mock_report_b in written_reports
    assert call_args[0][1] == "/output/report.pdf"


def test_pdf_engine_generate_with_iterable_data() -> None:
    """generate() passes non-dict data directly to the writer."""
    engine = PdfEngine()
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.pdf_config.clean_path = "/pdf_config.json"
    ctx.app_config.paths.pdf.clean_path = "/output/report.pdf"

    reports = [MagicMock(), MagicMock()]

    mock_writer = MagicMock()

    with (
        patch(
            "assets_guardian.core.domain.engines.pdf_engine.PDFBuilderRegistry.get_builders",
            return_value=[],
        ),
        patch(
            "assets_guardian.core.domain.engines.pdf_engine.PDFWriter",
            return_value=mock_writer,
        ),
    ):
        engine.generate(reports, ctx)

    # Iterable passed as-is
    call_args = mock_writer.write.call_args
    assert call_args[0][0] is reports


def test_pdf_engine_generate_calls_writer_with_correct_output_path() -> None:
    """generate() forwards the pdf output path from the context to the writer."""
    engine = PdfEngine()
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.pdf_config.clean_path = "/cfg/pdf_config.json"
    ctx.app_config.paths.pdf.clean_path = "/out/audit.pdf"

    mock_writer = MagicMock()

    with (
        patch(
            "assets_guardian.core.domain.engines.pdf_engine.PDFBuilderRegistry.get_builders",
            return_value=[],
        ),
        patch(
            "assets_guardian.core.domain.engines.pdf_engine.PDFWriter",
            return_value=mock_writer,
        ),
    ):
        engine.generate([], ctx)

    _, output_path = mock_writer.write.call_args[0]
    assert output_path == "/out/audit.pdf"
