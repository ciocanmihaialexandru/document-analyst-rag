"""Loaders cu registry + împărțire pe pachete pentru documentul CEC."""

import re
from pathlib import Path

import pdfplumber
from docx import Document as DocxDocument

LOADER_REGISTRY: dict[str, callable] = {}


def register_loader(ext: str):
    def decorator(func):
        LOADER_REGISTRY[ext.lower()] = func
        return func
    return decorator


def _page_clean(page) -> str:
    """Conținut curat al unei pagini: rânduri 'serviciu — valoare' din
    tabele, sau text normal dacă pagina n-are tabele."""
    parts: list[str] = []
    tables = page.extract_tables()
    if tables:
        for table in tables:
            for row in table:
                cells = [" ".join(c.split()) for c in row if c and c.strip()]
                if cells:
                    parts.append(" — ".join(cells))
    else:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n".join(parts)


@register_loader(".pdf")
def load_pdf(path: str) -> str:
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            c = _page_clean(page)
            if c:
                parts.append(c)
    return "\n".join(parts)


@register_loader(".txt")
def load_txt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


@register_loader(".docx")
def load_docx(path: str) -> str:
    doc = DocxDocument(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def load_document(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext not in LOADER_REGISTRY:
        raise ValueError(f"Format neacceptat: '{ext}'. Acceptate: {list(LOADER_REGISTRY)}")
    return LOADER_REGISTRY[ext](path)