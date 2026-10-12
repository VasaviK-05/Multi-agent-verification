from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def content_terms(text: str) -> set[str]:
    """Return normalized terms from text."""
    return {
        term
        for term in text.lower().split()
        if term
    }


class EvidenceRetriever:
    """Retrieve relevant evidence chunks from a FAISS index."""

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    MANIFEST_VERSION = 1

    def __init__(
        self,
        corpus_path: str = "data/evidence_corpus.json",
        index_dir: str | None = None,
        chunk_size: int = 500,
    ):
        self.corpus_path = Path(corpus_path)
        self.chunk_size = chunk_size

        if index_dir is None:
            index_dir = self.corpus_path.parent / "articles_13083_index"

        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "faiss.index"
        self.chunks_path = self.index_dir / "chunks.json"
        self.manifest_path = self.index_dir / "manifest.json"

        self.model = SentenceTransformer(self.EMBEDDING_MODEL)

        if self._index_is_current():
            self.index, self.chunks = self.load_index()
        else:
            self.index, self.chunks = self.build_index()
            self.save_index()

        self._document_frequency: Counter[str] | None = None

    def build_chunks(self) -> list[dict]:
        """Split corpus articles into chunks."""
        with self.corpus_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        chunks = []

        for article in data:
            article_id = article.get("id", article.get("article_id"))
            title = article.get("title", "")
            text = article.get("text", article.get("content", ""))
            url = article.get("url", "")

            words = text.split()

            for start in range(0, len(words), self.chunk_size):
                chunk_words = words[start:start + self.chunk_size]

                if not chunk_words:
                    continue

                chunks.append(
                    {
                        "article_id": article_id,
                        "title": title,
                        "text": " ".join(chunk_words),
                        "url": url,
                        "chunk_id": len(chunks),
                    }
                )

        return chunks

    def build_embeddings(self, chunks: list[dict]) -> np.ndarray:
        """Build normalized embeddings for evidence chunks."""
        texts = [
            f"{chunk.get('title', '')}\n{chunk.get('text', '')}"
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=len(texts) > 256,
            convert_to_numpy=True,
        )

        embeddings = np.ascontiguousarray(
            embeddings,
            dtype=np.float32,
        )

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
        if not (
            self.index_path.exists()
            and self.chunks_path.exists()
            and self.manifest_path.exists()
        ):
            return False

        try:
            with self.manifest_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                stored = json.load(file)

        except (OSError, json.JSONDecodeError):
            return False

        current = self._manifest()

        if stored.get("version") != current.get("version"):
            return False

        if stored.get("corpus_path") != current.get("corpus_path"):
            return False

        if stored.get("corpus_size") != current.get("corpus_size"):
            return False

        if abs(
            stored.get("corpus_mtime", 0)
            - current.get("corpus_mtime", 0)
        ) > 0.01:
            return False

        if stored.get("chunk_size") != current.get("chunk_size"):
            return False

        if stored.get("embedding_model") != current.get("embedding_model"):
            return False

        return True

    def save_index(self) -> None:
        """Save FAISS index, chunk metadata, and manifest to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        with self.chunks_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.chunks,
                file,
                ensure_ascii=False,
                indent=2,
            )

        with self.manifest_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self._manifest(),
                file,
                indent=2,
            )

    def load_index(self) -> tuple[faiss.Index, list[dict]]:
        """Load FAISS index and chunk metadata from disk."""
        index = faiss.read_index(
            str(self.index_path)
        )

        with self.chunks_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            chunks = json.load(file)

        return index, chunks

    # ------------------------------------------------------------------
    # Term statistics
    # ------------------------------------------------------------------

    def term_weights(self, terms: set[str]) -> dict[str, float]:
        """Smoothed IDF ``log((1 + N) / (1 + df))`` for terms that occur in the corpus.

        Terms absent from every chunk are omitted:no chunk can contain
        them, so they cannot tell an on-topic chunk from an off-topic one.
        """
        if self._document_frequency is None:
            frequency: Counter[str] = Counter()

            for chunk in self.chunks:
                frequency.update(
                    content_terms(
                        f"{chunk.get('title', '')} "
                        f"{chunk.get('text', '')}"
                    )
                )

            self._document_frequency = frequency

        total = len(self.chunks)

        return {
            term: math.log(
                (1 + total)
                / (1 + self._document_frequency[term])
            )
            for term in terms
            if self._document_frequency[term] > 0
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Retrieve the top-k evidence chunks for a query, best first.

        ``score`` is cosine similarity in [-1, 1].Fewer than ``k`` results
        are returned when the index holds fewer chunks.
        """
        total = int(self.index.ntotal)

        if total == 0 or k <= 0:
            return []

        k = min(k, total)

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
        )

        query_embedding = np.ascontiguousarray(
            query_embedding,
            dtype=np.float32,
        )

        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(
            query_embedding,
            k,
        )

        results = []

        for score, index_id in zip(
            scores[0],
            indices[0],
        ):
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