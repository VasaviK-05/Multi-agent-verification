"""Evidence corpus loading, chunking, embedding, and FAISS retrieval."""

import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


class EvidenceRetriever:
    """Loads evidence once and reuses the FAISS index for retrieval."""

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        corpus_path: str = "data/evidence_corpus.json",
        chunk_size: int = 500,
    ) -> None:
        self.corpus_path = Path(corpus_path)
        self.chunk_size = chunk_size

        # Load the embedding model only once.
        self.model = SentenceTransformer(self.EMBEDDING_MODEL)

        # Build the searchable evidence index only once.
        self.index, self.chunks = self.build_index()

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

        articles = self.load_corpus()
        chunks = []

        for article in articles:
            article_chunks = self.chunk_text(article["text"])

            for index, chunk in enumerate(article_chunks):
                chunks.append(
                    {
                        "article_id": article["id"],
                        "title": article["title"],
                        "url": article["url"],
                        "chunk_id": index,
                        "text": chunk,
                    }
                )

        return chunks

    def build_embeddings(self, chunks: list[dict]):
        """Create embeddings for all evidence chunks."""

        texts = [chunk["text"] for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
        )

        return embeddings

    def build_index(self):
        """Build a FAISS index from evidence embeddings."""

        chunks = self.build_chunks()

        embeddings = self.build_embeddings(chunks)

        # Normalize vectors so inner product behaves like cosine similarity.
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(embeddings.shape[1])

        index.add(embeddings)

        return index, chunks

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Retrieve the top-k evidence chunks for a query."""

        query_embedding = self.model.encode([query])

        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, k)

        results = []

        for score, index_id in zip(scores[0], indices[0]):
            results.append(
                {
                    "score": float(score),
                    "title": self.chunks[index_id]["title"],
                    "text": self.chunks[index_id]["text"],
                    "url": self.chunks[index_id]["url"],
                    "chunk_id": self.chunks[index_id]["chunk_id"],
                }
            )

        return results