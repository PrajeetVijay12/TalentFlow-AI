"""Turn an uploaded PDF / DOCX into plain text (all done locally)."""
from __future__ import annotations

import io


class ParseError(Exception):
    """A resume could not be read. The message is safe to show to the user."""


def extract_pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ParseError("The PDF is password-protected and cannot be read.")
        pages = [(p.extract_text() or "") for p in reader.pages]
    except ParseError:
        raise
    except (PyPdfError, ValueError, KeyError, OSError, AttributeError, TypeError):
        raise ParseError("Invalid or corrupted PDF file.") from None
    except Exception:  # pypdf can raise many odd errors on damaged files
        raise ParseError("Invalid or corrupted PDF file.") from None
    return "\n".join(pages)


def extract_docx_text(data: bytes) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        doc = Document(io.BytesIO(data))
        lines: list[str] = []
        for child in doc.element.body.iterchildren():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "p":
                lines.append(Paragraph(child, doc).text)
            elif tag == "tbl":
                for row in Table(child, doc).rows:
                    cells = []
                    for c in row.cells:
                        if c.text not in cells:
                            cells.append(c.text)
                    lines.append(" | ".join(t for t in cells if t.strip()))
    except Exception:
        raise ParseError("Invalid or corrupted DOCX file.") from None
    return "\n".join(lines)


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        text = extract_pdf_text(data)
    elif ext == "docx":
        text = extract_docx_text(data)
    else:
        raise ParseError("Unsupported file type. Please upload a PDF or DOCX resume.")
    if not text.strip():
        raise ParseError("The resume is empty or has no extractable text (scanned image PDFs are not supported).")
    return text
