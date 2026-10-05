"""Evidence corpus loading, chunking, embedding, and FAISS retrieval.

The FAISS index is persisted next to the corpus it was built from:

    <corpus dir>/evidence_index/<corpus stem>/faiss.index
    <corpus dir>/evidence_index/<corpus stem>/chunks.json
    <corpus dir>/evidence_index/<corpus stem>/manifest.json

The manifest records the corpus file (path, size, mtime), chunk size, and
embedding model. An index is reused only when the manifest matches, so a
retriever built on one corpus never answers from another corpus's index.

Retrieval scores are cosine similarities (inner product of L2-normalised
MiniLM vectors). FAISS always returns the nearest chunks; "nearest" is not
"relevant", so callers apply their own relevance cutoff.
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class EvidenceRetriever:
    """Loads evidence and uses a persistent, corpus-keyed FAISS index."""

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    MANIFEST_VERSION = 1

    def __init__(
        self,
        corpus_path: str = "data/evidence_corpus.json",
        chunk_size: int = 500,
        index_dir: str | Path | None = None,
        model: SentenceTransformer | None = None,
    ) -> None:
        self.corpus_path = Path(corpus_path)
        self.chunk_size = chunk_size

        if index_dir is None:
            index_dir = self.corpus_path.parent / "evidence_index" / self.corpus_path.stem
        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "faiss.index"
        self.chunks_path = self.index_dir / "chunks.json"
        self.manifest_path = self.index_dir / "manifest.json"

        self.model = model or SentenceTransformer(self.EMBEDDING_MODEL)

        if self._index_is_current():
            self.index, self.chunks = self.load_index()
        else:
            self.index, self.chunks = self.build_index()
            self.save_index()

    # ------------------------------------------------------------------
    # Corpus and chunks
    # ------------------------------------------------------------------

    def load_corpus(self) -> list[dict]:
        """Load articles from the local evidence corpus."""
        with self.corpus_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def chunk_text(self, text: str) -> list[str]:
        """Split text into fixed-size word chunks."""
        words = text.split()
        return [
            " ".join(words[i : i + self.chunk_size])
            for i in range(0, len(words), self.chunk_size)
        ]

    def build_chunks(self) -> list[dict]:
        """Convert articles into searchable evidence chunks."""
        chunks = []
        for article in self.load_corpus():
            for index, chunk in enumerate(self.chunk_text(article.get("text", ""))):
                chunks.append(
                    {
                        "article_id": article.get("id"),
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "chunk_id": index,
                        "text": chunk,
                    }
                )
        return chunks

    # ------------------------------------------------------------------
    # Index
    # ------------------------------------------------------------------

    def build_embeddings(self, chunks: list[dict]) -> np.ndarray:
        """Create L2-normalised float32 embeddings for all evidence chunks."""
        texts = [chunk["text"] for chunk in chunks]
        if not texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=len(texts) > 256,
            convert_to_numpy=True,
        )
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)
        return embeddings

    def build_index(self) -> tuple[faiss.Index, list[dict]]:
        """Build a FAISS inner-product index from evidence embeddings."""
        chunks = self.build_chunks()
        embeddings = self.build_embeddings(chunks)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        if len(chunks):
            index.add(embeddings)
        return index, chunks

    def _manifest(self) -> dict:
        stat = self.corpus_path.stat()
        return {
            "version": self.MANIFEST_VERSION,
            "corpus_path": str(self.corpus_path.resolve()),
            "corpus_size": stat.st_size,
            "corpus_mtime": stat.st_mtime,
            "chunk_size": self.chunk_size,
            "embedding_model": self.EMBEDDING_MODEL,
        }

    def _index_is_current(self) -> bool:
        if not (self.index_path.exists() and self.chunks_path.exists() and self.manifest_path.exists()):
            return False
        try:
            with self.manifest_path.open("r", encoding="utf-8") as file:
                stored = json.load(file)
        except (OSError, json.JSONDecodeError):
            return False
        return stored == self._manifest()

    def save_index(self) -> None:
        """Save FAISS index, chunk metadata, and manifest to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with self.chunks_path.open("w", encoding="utf-8") as file:
            json.dump(self.chunks, file, ensure_ascii=False, indent=2)
        with self.manifest_path.open("w", encoding="utf-8") as file:
            json.dump(self._manifest(), file, indent=2)

    def load_index(self) -> tuple[faiss.Index, list[dict]]:
        """Load FAISS index and chunk metadata from disk."""
        index = faiss.read_index(str(self.index_path))
        with self.chunks_path.open("r", encoding="utf-8") as file:
            chunks = json.load(file)
        return index, chunks

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Retrieve the top-k evidence chunks for a query, best first.

        ``score`` is cosine similarity in [-1, 1]. Fewer than ``k`` results
        are returned when the index holds fewer chunks.
        """
        total = int(self.index.ntotal)
        if total == 0 or k <= 0:
            return []
        k = min(k, total)

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(
            query_embedding,
            k,
        )

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
