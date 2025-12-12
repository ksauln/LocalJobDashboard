import re
from pathlib import Path

from bs4 import BeautifulSoup
import pypdf
from docx import Document


def extract_text(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = pypdf.PdfReader(str(file_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in {".docx", ".doc"}:
        doc = Document(str(file_path))
        text = "\n".join(p.text for p in doc.paragraphs)
    elif suffix in {".txt"}:
        text = file_path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_html(text: str) -> str:
    """Convert HTML into readable plain text for display/scoring."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(" ", strip=True)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()
