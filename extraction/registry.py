"""Registry de extractoare per tip de document (doc_type).

Framework-ul (pipeline) rămâne generic și întreabă registry-ul:
fiecare doc_type își aduce schema, splitter-ul, prompt-ul și asamblarea.
"""
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel


@dataclass
class DocExtractor:
    doc_type: str
    section_schema: type[BaseModel]                         # ce extragem dintr-o secțiune (ex: Pachet)
    document_schema: type[BaseModel]                        # schema întregului document (ex: DocumentComisioane)
    split: Callable[[str], list[tuple[str, str]]]           # path -> [(nume, text), ...]
    build_prompt: Callable[[str, str], str]                 # (nume, text) -> prompt LLM
    assemble: Callable[[list[BaseModel], str], BaseModel]   # (secțiuni_extrase, full_text) -> document
    section_label: str = "Secțiune"                         # eticheta pusă în chunk


EXTRACTOR_REGISTRY: dict[str, DocExtractor] = {}


def register_extractor(ext: DocExtractor) -> None:
    EXTRACTOR_REGISTRY[ext.doc_type] = ext


def get_extractor(doc_type: str) -> DocExtractor:
    if doc_type not in EXTRACTOR_REGISTRY:
        raise KeyError(
            f"Nu există extractor pentru doc_type='{doc_type}'. "
            f"Disponibile: {list(EXTRACTOR_REGISTRY)}"
        )
    return EXTRACTOR_REGISTRY[doc_type]