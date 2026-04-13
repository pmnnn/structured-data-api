import io
import logging

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts raw text from a PDF file (bytes) page by page.
    Tries PyMuPDF first (better LaTeX/Type1 font support),
    falls back to pdfplumber.
    """
    full_text = _extract_with_pymupdf(file_bytes) or _extract_with_pdfplumber(file_bytes)

    if not full_text.strip():
        raise ValueError(
            "The PDF contains no extractable text. "
            "Try using the /extract/text endpoint with plain text instead."
        )

    logger.info("PDF extracted: %d characters", len(full_text))
    return full_text


def _extract_with_pymupdf(file_bytes: bytes) -> str:
    try:
        import fitz  # pymupdf

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                pages_text.append(f"--- Page {i} ---\n{text}")
        doc.close()
        result = "\n\n".join(pages_text)
        if result.strip():
            logger.info("PDF extracted via PyMuPDF")
        return result
    except ImportError:
        logger.warning("PyMuPDF not available, falling back to pdfplumber")
        return ""
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed (%s), falling back to pdfplumber", exc)
        return ""


def _extract_with_pdfplumber(file_bytes: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    pages_text.append(f"--- Page {i} ---\n{text}")
            result = "\n\n".join(pages_text)
            if result.strip():
                logger.info("PDF extracted via pdfplumber")
            return result
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts raw text from a DOCX file (bytes).
    """
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)

        if not full_text.strip():
            raise ValueError("The DOCX file appears to be empty.")

        logger.info("DOCX extracted: %d characters", len(full_text))
        return full_text

    except Exception as exc:
        raise ValueError(f"Could not read DOCX: {exc}") from exc
