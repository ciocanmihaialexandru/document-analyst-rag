"""Repository pentru Document + DocumentChunk: CRUD + similarity search."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Document, DocumentChunk


class DocumentRepository:
    """Operații pe documente și chunks, inclusiv căutare vectorială."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- CREATE ----
    def create_document(
        self, filename: str, doc_type: str, extracted: dict | None
    ) -> Document:
        doc = Document(filename=filename, doc_type=doc_type, extracted=extracted)
        self.db.add(doc)
        self.db.flush()        # obține doc.id; commit-ul se face în transaction()
        return doc

    def add_chunks(self, document_id: int, chunks: list[dict]) -> list[DocumentChunk]:
        """chunks: [{'chunk_index': int, 'content': str, 'embedding': list[float]}, ...]"""
        objs = [DocumentChunk(document_id=document_id, **c) for c in chunks]
        self.db.add_all(objs)
        self.db.flush()
        return objs

    # ---- READ ----
    def list_documents(self) -> list[Document]:
        return list(self.db.execute(select(Document)).scalars())

    def get_document(self, document_id: int) -> Document | None:
        return self.db.get(Document, document_id)

    # ---- SEARCH (pgvector) ----
    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        package: str | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Caută chunks similare; opțional, doar într-un anumit pachet."""
        score = (
            1 - DocumentChunk.embedding.cosine_distance(query_embedding)
        ).label("score")

        stmt = select(DocumentChunk, score)
        if package:
            stmt = stmt.where(DocumentChunk.package == package)   # filtru metadata
        stmt = stmt.order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        rows = self.db.execute(stmt).all()
        return [(chunk, float(s)) for chunk, s in rows]

    # ---- DELETE ----
    def delete_all(self) -> int:
        """Șterge toate documentele (și chunk-urile, prin cascade)."""
        docs = self.list_documents()
        for d in docs:
            self.db.delete(d)
        return len(docs)