"""Evidence corpus loading, chunking, and FAISS retrieval."""

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class EvidenceRetriever:
    """Loads a local corpus and retrieves the most similar chunks."""

    def __init__(
        self,
        corpus_path: str = "data/evidence_corpus.json",
        chunk_size: int = 120,
        chunk_overlap: int = 20,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.corpus_path = Path(corpus_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name

        self.model: SentenceTransformer | None = None
        self.index: faiss.Index | None = None
        self.chunks: list[dict] = []

    def load_corpus(self) -> list[dict]:
        with self.corpus_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def chunk_text(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []

        step = self.chunk_size - self.chunk_overlap
        chunks = []

        for start in range(0, len(words), step):
            piece = words[start : start + self.chunk_size]
            chunks.append(" ".join(piece))
            if start + self.chunk_size >= len(words):
                break

        return chunks

    def build_chunks(self) -> list[dict]:
        chunks = []

        for article in self.load_corpus():
            for index, text in enumerate(self.chunk_text(article.get("text", ""))):
                chunks.append(
                    {
                        "article_id": article.get("id"),
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "chunk_id": index,
                        "text": text,
                    }
                )

        return chunks

    def _ensure_index(self) -> None:
        """Embed the corpus and build FAISS on the first query only."""
        if self.index is not None:
            return

        self.model = SentenceTransformer(self.model_name)
        self.chunks = self.build_chunks()

        if not self.chunks:
            self.index = faiss.IndexFlatIP(self.model.get_sentence_embedding_dimension())
            return

        embeddings = self.model.encode(
            [chunk["text"] for chunk in self.chunks],
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)

        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        self._ensure_index()

        if self.index.ntotal == 0:
            return []

        k = min(k, self.index.ntotal)
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
        )
        query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, k)
        results = []

        for score, index_id in zip(scores[0], indices[0]):
            if index_id < 0:
                continue

            chunk = self.chunks[int(index_id)]
            results.append(
                {
                    "score": float(score),
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "url": chunk["url"],
                    "chunk_id": chunk["chunk_id"],
                }
            )

        return results