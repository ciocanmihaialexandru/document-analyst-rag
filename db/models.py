"""Modele SQLAlchemy: Document (1) -> DocumentChunk (N)."""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, JSON, func,
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from db.database import Base

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 = 384 dimensiuni


class Document(Base):
    """Un document încărcat (ex: PDF-ul CEC)."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False, default="comisioane")
    extracted = Column(JSON, nullable=True)        # DocumentComisioane.model_dump()
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # un document are multe chunks; ștergerea documentului șterge chunk-urile
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    """O bucată de text dintr-un document, cu embedding pentru căutare."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index = Column(Integer, nullable=False)   # ordinea în document
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    package = Column(String(100), nullable=True, index=True)

    document = relationship("Document", back_populates="chunks")