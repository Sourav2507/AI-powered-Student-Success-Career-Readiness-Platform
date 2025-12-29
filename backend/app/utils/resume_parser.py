import os
import pdfplumber
import docx


SUPPORTED_EXTENSIONS = (".pdf", ".docx")


def extract_text(file_path: str) -> str:
    """
    Extract text from a resume file (PDF or DOCX).

    Args:
        file_path (str): Path to resume file

    Returns:
        str: Extracted plain text
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    file_path = file_path.lower()

    if file_path.endswith(".pdf"):
        return _extract_from_pdf(file_path)

    elif file_path.endswith(".docx"):
        return _extract_from_docx(file_path)

    else:
        raise ValueError(
            f"Unsupported file format. Supported formats: {SUPPORTED_EXTENSIONS}"
        )


def _extract_from_pdf(file_path: str) -> str:
    text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

    return "\n".join(text).strip()


def _extract_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)

    text = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(text).strip()
