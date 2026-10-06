"""Extractor specific documentului CEC (comisioane pe pachete).
Tot ce e legat de formatul CEC trăiește AICI, izolat."""

import re
import pdfplumber

from extraction.registry import DocExtractor, register_extractor
from extraction.loaders import _page_clean
from extraction.schemas import Pachet, DocumentComisioane

# marcajul de început al unui pachet: 'Denumirea contului: Pachet "X" în LEI'
_PACKAGE_RE = re.compile(
    r'Denumirea contului:\s*Pachet\s*[“"]?\s*(.+?)\s*[”"]?\s*[îi]n LEI',
    re.IGNORECASE,
)


def split_cec(path: str) -> list[tuple[str, str]]:
    """Împarte PDF-ul CEC în secțiuni per pachet: [(nume_pachet, text_curat), ...]."""
    sections: list[tuple[str, str]] = []
    name: str | None = None
    buf: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text() or ""
            m = _PACKAGE_RE.search(raw)
            if m:
                if name is not None:
                    sections.append((name, "\n".join(buf)))
                name = m.group(1).strip()
                buf = []
            c = _page_clean(page)
            if c:
                buf.append(c)
    if name is not None:
        sections.append((name, "\n".join(buf)))
    return sections


def build_prompt_cec(nume: str, text: str) -> str:
    return (
        f"Extrage comisioanele pentru pachetul '{nume}' din textul de mai jos. "
        f"Pune nume='{nume}' și completează lista de comisioane "
        f"(serviciu, categorie, valoare).\n\nText:\n{text}"
    )


def _detect_meta(full_text: str) -> tuple[str, str | None]:
    banca = "CEC Bank S.A."
    m = re.search(r"Denumirea furnizorului contului:\s*(.+)", full_text)
    if m:
        banca = m.group(1).strip()
    data = None
    m = re.search(r"\bData:\s*([\d.]{6,})", full_text)
    if m:
        data = m.group(1).strip()
    return banca, data


def assemble_cec(pachete: list[Pachet], full_text: str) -> DocumentComisioane:
    banca, data = _detect_meta(full_text)
    return DocumentComisioane(banca=banca, data=data, pachete=pachete)


# înregistrarea plugin-ului — rulează la `import extraction.doc_types.cec`
register_extractor(DocExtractor(
    doc_type="cec_comisioane",
    section_schema=Pachet,
    document_schema=DocumentComisioane,
    split=split_cec,
    build_prompt=build_prompt_cec,
    assemble=assemble_cec,
    section_label="Pachet",
))