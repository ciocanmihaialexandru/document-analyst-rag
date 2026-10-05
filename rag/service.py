"""RAGService: embeddings (sentence-transformers) + similarity search."""

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from db.repository import DocumentRepository
from db.models import DocumentChunk

# model multilingv (merge bine pe română), 384 dimensiuni
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class RAGService:
    """Embeddings + căutare vectorială, cu lazy loading pentru model."""

    _model: SentenceTransformer | None = None  # singleton per proces

    def __init__(self, db: Session) -> None:
        self.repo = DocumentRepository(db)

    @property
    def model(self) -> SentenceTransformer:
        """Modelul se încarcă o singură dată (prima utilizare)."""
        if RAGService._model is None:
            print(f"Încărcare model {MODEL_NAME}...")
            RAGService._model = SentenceTransformer(MODEL_NAME)
        return RAGService._model

    def embed(self, text: str) -> list[float]:
        """Un text -> un vector de 384 de numere."""
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Mai multe texte deodată (mai eficient decât unul câte unul)."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]

    def search(self, query: str, top_k: int = 5, package: str | None = None) -> list[tuple[DocumentChunk, float]]:
        query_embedding = self.embed(query)
        return self.repo.similarity_search(query_embedding, top_k=top_k, package=package)