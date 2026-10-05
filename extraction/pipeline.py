"""Pipeline: split pe pachete -> extract per pachet -> chunk etichetat -> store + JSON."""

import re
from pathlib import Path

from langchain_openai import ChatOpenAI

from extraction.loaders import split_packages, load_document
from extraction.chunker import chunk_text
from extraction.schemas import Pachet, DocumentComisioane
from db.database import transaction
from db.repository import DocumentRepository
from rag.service import RAGService

LITELLM_BASE_URL = "http://localhost:4000/v1"
EXTRACT_MODEL = "claude"      # sau "gemini"


def get_llm(model: str = EXTRACT_MODEL) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=LITELLM_BASE_URL, api_key="local", model=model, temperature=0
    )


def extract_package(text: str, nume: str, model: str = EXTRACT_MODEL) -> Pachet:
    """Extrage comisioanele unui singur pachet (apel LLM mic, pe o secțiune)."""
    llm = get_llm(model).with_structured_output(Pachet)
    prompt = (
        f"Extrage comisioanele pentru pachetul '{nume}' din textul de mai jos. "
        f"Pune nume='{nume}' și completează lista de comisioane "
        f"(serviciu, categorie, valoare).\n\nText:\n{text}"
    )
    return llm.invoke(prompt)


def _detect_meta(full_text: str) -> tuple[str, str | None]:
    """Scoate banca și data din document (regex simplu, fără LLM)."""
    banca = "CEC Bank S.A."
    m = re.search(r"Denumirea furnizorului contului:\s*(.+)", full_text)
    if m:
        banca = m.group(1).strip()
    data = None
    m = re.search(r"\bData:\s*([\d.]{6,})", full_text)
    if m:
        data = m.group(1).strip()
    return banca, data


def process(file_path: str, model: str = EXTRACT_MODEL) -> dict:
    path = Path(file_path)

    # 1. SPLIT pe pachete (fallback: tot documentul = un singur "pachet")
    sections = split_packages(str(path))
    if not sections:
        sections = [("Document", load_document(str(path)))]

    full_text = load_document(str(path))
    banca, data = _detect_meta(full_text)

    pachete: list[Pachet] = []
    chunks_data: list[dict] = []   # {content, package}

    for nume, text in sections:
        print(f"  extrag pachetul: {nume} ...")
        pachete.append(extract_package(text, nume, model))
        for c in chunk_text(text, chunk_size=800, overlap=100):
            chunks_data.append({"content": f"[Pachet {nume}] {c}", "package": nume})

    doc_data = DocumentComisioane(banca=banca, data=data, pachete=pachete)

    with transaction() as db:
        rag = RAGService(db)
        repo = DocumentRepository(db)

        contents = [cd["content"] for cd in chunks_data]
        embeddings = rag.embed_batch(contents)

        doc = repo.create_document(path.name, "comisioane", doc_data.model_dump())
        repo.add_chunks(
            doc.id,
            [
                {
                    "chunk_index": i,
                    "content": cd["content"],
                    "embedding": e,
                    "package": cd["package"],
                }
                for i, (cd, e) in enumerate(zip(chunks_data, embeddings))
            ],
        )
        doc_id = doc.id

    # 4. SALVARE JSON
    out_path = path.with_name(f"{path.stem}_extracted.json")
    out_path.write_text(doc_data.model_dump_json(indent=2), encoding="utf-8")

    return {
        "document_id": doc_id,
        "pachete": len(pachete),
        "comisioane_total": sum(len(p.comisioane) for p in pachete),
        "chunks": len(chunks_data),
        "json": str(out_path),
    }