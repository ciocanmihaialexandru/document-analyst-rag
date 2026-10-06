"""Pipeline GENERIC: split -> extract per secțiune -> chunk etichetat -> store + JSON.
Specificul fiecărui tip de document vine din registry (doc_type)."""

from pathlib import Path

from langchain_openai import ChatOpenAI

from extraction.registry import get_extractor
from extraction.loaders import load_document
from extraction.chunker import chunk_text
from db.database import transaction
from db.repository import DocumentRepository
from rag.service import RAGService

# înregistrează extractoarele disponibile (efect secundar la import)
import extraction.doc_types.cec  # noqa: F401

LITELLM_BASE_URL = "http://localhost:4000/v1"
EXTRACT_MODEL = "claude"


def get_llm(model: str = EXTRACT_MODEL) -> ChatOpenAI:
    return ChatOpenAI(base_url=LITELLM_BASE_URL, api_key="local", model=model, temperature=0)


def process(file_path: str, doc_type: str = "cec_comisioane", model: str = EXTRACT_MODEL) -> dict:
    path = Path(file_path)
    ext = get_extractor(doc_type)

    # 1. SPLIT (specific doc_type); fallback: tot documentul = o singură secțiune
    sections = ext.split(str(path))
    if not sections:
        sections = [("Document", load_document(str(path)))]

    full_text = load_document(str(path))

    # 2. EXTRACT structurat per secțiune + chunk etichetat
    llm = get_llm(model).with_structured_output(ext.section_schema)
    extrase = []
    chunks_data: list[dict] = []

    for nume, text in sections:
        print(f"  extrag: {nume} ...")
        extrase.append(llm.invoke(ext.build_prompt(nume, text)))
        for c in chunk_text(text, chunk_size=800, overlap=100):
            chunks_data.append({"content": f"[{ext.section_label} {nume}] {c}", "package": nume})

    # 3. ASSEMBLE documentul (specific doc_type)
    doc_data = ext.assemble(extrase, full_text)

    # 4. STORE
    with transaction() as db:
        rag = RAGService(db)
        repo = DocumentRepository(db)
        contents = [cd["content"] for cd in chunks_data]
        embeddings = rag.embed_batch(contents)
        doc = repo.create_document(path.name, doc_type, doc_data.model_dump())
        repo.add_chunks(doc.id, [
            {"chunk_index": i, "content": cd["content"], "embedding": e, "package": cd["package"]}
            for i, (cd, e) in enumerate(zip(chunks_data, embeddings))
        ])
        doc_id = doc.id

    # 5. JSON
    out_path = path.with_name(f"{path.stem}_extracted.json")
    out_path.write_text(doc_data.model_dump_json(indent=2), encoding="utf-8")

    return {
        "document_id": doc_id,
        "sectiuni": len(extrase),
        "chunks": len(chunks_data),
        "doc_type": doc_type,
        "json": str(out_path),
    }