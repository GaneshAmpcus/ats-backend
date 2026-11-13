import io
import re
import unicodedata
import zipfile

MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_INLINE_SPACE = re.compile(r"[ \t]+")
_SPACE_AROUND_NEWLINE = re.compile(r" *\n *")
_BLANK_LINES = re.compile(r"\n{3,}")


def _resolve(obj):
    getter = getattr(obj, "get_object", None)
    return getter() if callable(getter) else obj


def _pdf_page_links(page) -> list[str]:
    """Return external URLs from a page's link annotations (e.g. LinkedIn/GitHub)."""
    links: list[str] = []
    try:
        annots = page.get("/Annots")
        if annots is None:
            return links
        for annot in _resolve(annots):
            action = _resolve(annot).get("/A")
            if action is None:
                continue
            uri = _resolve(action).get("/URI")
            if uri:
                links.append(str(_resolve(uri)))
    except Exception:
        # Links are a best-effort extra; never fail text extraction because of them.
        pass
    return links


def _docx_links(document) -> list[str]:
    try:
        return [
            rel.target_ref
            for rel in document.part.rels.values()
            if rel.is_external and rel.reltype.endswith("/hyperlink")
        ]
    except Exception:
        return []


def _append_links(text: str, links: list[str]) -> str:
    """Append hyperlink targets that are not already visible in the text.

    Resumes often show "LinkedIn" as the link label while the URL only lives in the
    link annotation, so it would otherwise never reach the AI service.
    """
    if not text.strip():
        return text
    lowered = text.lower()
    seen: set[str] = set()
    extra: list[str] = []
    for link in links:
        link = link.strip()
        key = link.rstrip("/").lower()
        if not key.startswith(("http://", "https://")) or key in seen or key in lowered:
            continue
        seen.add(key)
        extra.append(link)
    if not extra:
        return text
    return text + "\n\nLinks:\n" + "\n".join(extra)


class ExtractionError(Exception):
    """Raised when text cannot be extracted. The message is safe to show to users."""


def clean_text(text: str, *, max_chars: int | None = None) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)
    text = _INLINE_SPACE.sub(" ", text)
    text = _SPACE_AROUND_NEWLINE.sub("\n", text)
    text = _BLANK_LINES.sub("\n\n", text)
    text = text.strip()
    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars].rstrip()
    return text


def _extract_pdf(data: bytes, max_pages: int) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ExtractionError("The PDF is password protected.")
        if len(reader.pages) > max_pages:
            raise ExtractionError(f"The PDF has more than {max_pages} pages.")
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        links = [link for page in reader.pages for link in _pdf_page_links(page)]
        return _append_links(text, links)
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("The PDF could not be read.") from exc


def _extract_docx(data: bytes) -> str:
    from docx import Document

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(info.file_size for info in archive.infolist()) > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise ExtractionError("The DOCX file is too large once decompressed.")

        document = Document(io.BytesIO(data))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return _append_links("\n".join(parts), _docx_links(document))
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("The DOCX file could not be read.") from exc


def _extract_txt(data: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    raise ExtractionError("The text file could not be decoded.")


def extract_text(data: bytes, extension: str, *, max_pdf_pages: int, max_chars: int) -> str:
    extension = extension.lower()
    if extension == ".pdf":
        raw = _extract_pdf(data, max_pdf_pages)
    elif extension == ".docx":
        raw = _extract_docx(data)
    elif extension == ".txt":
        raw = _extract_txt(data)
    else:
        raise ExtractionError(f"Unsupported file type: {extension}")

    cleaned = clean_text(raw, max_chars=max_chars)
    if not cleaned:
        raise ExtractionError(
            "No extractable text was found. The file may be a scanned image."
        )
    return cleaned
