import io

import pytest

from app.modules.resumes.extraction import ExtractionError, clean_text, extract_text


def test_clean_text_normalizes_whitespace_and_control_characters() -> None:
    raw = "Jane\x00 Doe \r\n\r\n\r\n\r\n  Python   \t Developer \u00a0 "

    assert clean_text(raw) == "Jane Doe\n\nPython Developer"


def test_clean_text_truncates_to_max_chars() -> None:
    assert clean_text("a" * 50, max_chars=10) == "a" * 10


def test_extract_txt_decodes_utf8_with_bom() -> None:
    data = "\ufeffJane Doe\nEngineer".encode("utf-8")

    assert extract_text(data, ".txt", max_pdf_pages=5, max_chars=1000) == "Jane Doe\nEngineer"


def test_extract_rejects_blank_content() -> None:
    with pytest.raises(ExtractionError, match="No extractable text"):
        extract_text(b"  \n  ", ".txt", max_pdf_pages=5, max_chars=1000)


def test_extract_docx_reads_paragraphs_and_tables() -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("Jane Doe")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Python"
    table.rows[0].cells[1].text = "FastAPI"
    buffer = io.BytesIO()
    document.save(buffer)

    text = extract_text(buffer.getvalue(), ".docx", max_pdf_pages=5, max_chars=1000)

    assert "Jane Doe" in text
    assert "Python | FastAPI" in text


def test_extract_pdf_rejects_corrupt_file() -> None:
    pytest.importorskip("pypdf")

    with pytest.raises(ExtractionError, match="could not be read"):
        extract_text(b"%PDF-1.4 not really a pdf", ".pdf", max_pdf_pages=5, max_chars=1000)


def test_extract_pdf_with_no_text_reports_scanned_file() -> None:
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(ExtractionError, match="scanned image"):
        extract_text(buffer.getvalue(), ".pdf", max_pdf_pages=5, max_chars=1000)


def test_extract_pdf_enforces_page_limit() -> None:
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(ExtractionError, match="more than 2 pages"):
        extract_text(buffer.getvalue(), ".pdf", max_pdf_pages=2, max_chars=1000)
