"""Evidence corpus loading, chunking, embedding, and FAISS retrieval.

The FAISS index is persisted next to the corpus it was built from:

    <corpus dir>/evidence_index/<corpus stem>/faiss.index
    <corpus dir>/evidence_index/<corpus stem>/chunks.json
    <corpus dir>/evidence_index/<corpus stem>/manifest.json

The manifest records the corpus file (path, size, mtime, SHA-256 of its
bytes), chunk size, and embedding model. An index is reused only when the
content hash, chunk size and model match, so a retriever built on one
corpus never answers from another corpus's index, and a same-size edit
that keeps the timestamp still triggers a rebuild. A legacy manifest
without a content hash is never trusted and causes a one-time rebuild.

Versions and source identifiers
    corpus_version  "sha256:<hex>" of the corpus file bytes.
    index_version   "idx-<12 hex>" over corpus_version, chunk size and
                    embedding model: chunk boundaries and vectors depend on
                    all three.
    article_id      the corpus's own ``id``, as a string. Only meaningful
                    within one corpus_version (a regenerated file may
                    number its articles differently).
    article_key     the article independent of any corpus file: "wiki:<page>"
                    from a Wikipedia URL, "url:<url>" for another URL, and
                    "corpus:<corpus hash>:<article_id>" when there is no URL
                    (``article_key_scope`` says which: "global" or "corpus").
    source_id       "<article_key>#<12 hex of SHA-256 of the chunk text>".
                    Equal on every machine for identical text; different
                    text never shares one, so two results only share a
                    source_id when they used the same words.
    index_ref       "<index_version>:<article_id>:<chunk_id>", the chunk's
                    position in this exact index build.

Retrieval scores are cosine similarities (inner product of L2-normalised
MiniLM vectors). FAISS always returns the nearest chunks; "nearest" is not
"relevant", so callers apply their own relevance cutoff. ``retrieve`` also
adds the best BM25 keyword matches for the same query, marked
``lexical_hit``, so a passage the embedding model ranks low can still be
offered to that cutoff. ``score`` stays the cosine.

``term_weights`` exposes inverse document frequencies over the chunks
(title + text) so callers can tell distinctive terms ("Europa", "Brann")
from common ones ("league", "final") when checking a chunk's topic.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

STOPWORDS = frozenset(
    """
    a an and are as at be been being but by can could did do does for from had
    has have he her his how i if in into is it its may might of on or our she
    should so than that the their them then there these they this those to was
    we were what when where which while who whom whose why will with would you
    your about after also any before both each more most not other over same
    some such only own very just name named list give tell
    """.split()
)

_TOKEN = re.compile(r"[a-z0-9]+")

DEFAULT_CORPUS_PATH = "data/evidence_corpus.json"


def default_corpus_path() -> str:
    """Article file for a retriever or verifier constructed without ``corpus_path``.

    Reads ``EVIDENCE_CORPUS_PATH`` from the environment (and ``.env``). Falls
    back to ``data/evidence_corpus.json`` when the variable is unset.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    return os.getenv("EVIDENCE_CORPUS_PATH", DEFAULT_CORPUS_PATH)


def file_sha256(path: Path) -> str:
    """Hex SHA-256 of a file's bytes, read in 1 MiB blocks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def article_key(url: str | None, article_id: str | None, corpus_version: str) -> tuple[str, str]:
    """(key, scope) naming an article independently of row order where possible.

    Scope "global": the key comes from the URL and is the same in any corpus
    that contains the page. Scope "corpus": no URL, so the key is only valid
    for this corpus file.
    """
    parsed = urlparse(url or "")
    if parsed.netloc.endswith("wikipedia.org") and parsed.path.startswith("/wiki/"):
        return f"wiki:{unquote(parsed.path[len('/wiki/'):])}", "global"
    if parsed.scheme and parsed.netloc:
        return f"url:{url}", "global"
    corpus_hash = corpus_version.split(":", 1)[-1][:12]
    return f"corpus:{corpus_hash}:{article_id}", "corpus"


def content_terms(text: str) -> set[str]:
    """Lowercase content tokens: numbers, and words of 3+ letters not in STOPWORDS."""
    return set(_content_counts(text))


def _content_counts(text: str) -> Counter[str]:
    """Term frequencies for the same tokens ``content_terms`` keeps."""
    return Counter(
        token
        for token in _TOKEN.findall(str(text).lower())
        if token.isdigit() or (len(token) >= 3 and token not in STOPWORDS)
    )


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
    MANIFEST_VERSION = 2
    # Standard BM25 parameters (Robertson). Not fitted to any question.
    BM25_K1 = 1.5
    BM25_B = 0.75

    def __init__(
        self,
        corpus_path: str | None = None,
        chunk_size: int = 500,
        index_dir: str | Path | None = None,
        model: SentenceTransformer | None = None,
    ) -> None:
        if corpus_path is None:
            corpus_path = default_corpus_path()
        self.corpus_path = Path(corpus_path)
        if not self.corpus_path.is_file():
            raise FileNotFoundError(
                f"Evidence corpus not found: {self.corpus_path.resolve()}. Set "
                f"EVIDENCE_CORPUS_PATH (environment or .env) to an existing article JSON "
                f"file, or unset it to use the bundled {DEFAULT_CORPUS_PATH}."
            )
        self.chunk_size = chunk_size
        self.corpus_version = f"sha256:{file_sha256(self.corpus_path)}"
        self.index_version = "idx-" + text_sha256(
            json.dumps([self.corpus_version, self.chunk_size, self.EMBEDDING_MODEL])
        )[:12]

        if index_dir is None:
            index_dir = self.corpus_path.parent / "articles_13083_index"

        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "faiss.index"
        self.chunks_path = self.index_dir / "chunks.json"
        self.manifest_path = self.index_dir / "manifest.json"

        self.model = model or SentenceTransformer(self.EMBEDDING_MODEL)
        self._document_frequency: Counter[str] | None = None
        self._postings: dict[str, list[tuple[int, int]]] | None = None
        self._doc_lengths: list[int] = []
        self._avgdl = 0.0

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

    # Fields that decide whether a stored index still matches the corpus.
    _MANIFEST_KEYS = ("version", "corpus_sha256", "chunk_size", "embedding_model")

    def _manifest(self) -> dict:
        stat = self.corpus_path.stat()

        return {
            "version": self.MANIFEST_VERSION,
            "corpus_path": str(self.corpus_path.resolve()),
            "corpus_size": stat.st_size,
            "corpus_mtime": stat.st_mtime,
            "corpus_sha256": self.corpus_version.split(":", 1)[1],
            "corpus_version": self.corpus_version,
            "index_version": self.index_version,
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
        # Never accept a legacy size/mtime-only manifest: replacing a corpus
        # with same-size bytes while preserving its timestamp would otherwise
        # reuse stale chunks and vectors.
        matches = all(stored.get(key) == current[key] for key in self._MANIFEST_KEYS)
        if matches and stored != current:
            self._write_manifest(current)
        return matches

    def _write_manifest(self, manifest: dict) -> None:
        with self.manifest_path.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=2)

    def save_index(self) -> None:
        """Save FAISS index, chunk metadata, and manifest to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with self.chunks_path.open("w", encoding="utf-8") as file:
            json.dump(self.chunks, file, ensure_ascii=False, indent=2)
        self._write_manifest(self._manifest())

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

        Terms absent from every chunk are omitted: no chunk can contain
        them, so they cannot tell an on-topic chunk from an off-topic one.
        """
        if self._document_frequency is None:
            frequency: Counter[str] = Counter()
            for chunk in self.chunks:
                frequency.update(content_terms(f"{chunk.get('title', '')} {chunk.get('text', '')}"))
            self._document_frequency = frequency
        total = len(self.chunks)
        return {
            term: math.log((1 + total) / (1 + self._document_frequency[term]))
            for term in terms
            if self._document_frequency[term] > 0
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _ensure_lexical_index(self) -> None:
        """Build term postings for BM25 once from the loaded chunks."""
        if self._postings is not None:
            return
        postings: dict[str, list[tuple[int, int]]] = {}
        lengths: list[int] = []
        for index, chunk in enumerate(self.chunks):
            counts = _content_counts(f"{chunk.get('title', '')} {chunk.get('text', '')}")
            lengths.append(sum(counts.values()))
            for term, frequency in counts.items():
                postings.setdefault(term, []).append((index, frequency))
        self._postings = postings
        self._doc_lengths = lengths
        self._avgdl = (sum(lengths) / len(lengths)) if lengths else 0.0

    def _lexical_top(self, query: str, k: int) -> list[tuple[int, float]]:
        """Highest BM25 chunk ids for ``query``. Scores are positive only."""
        self._ensure_lexical_index()
        if not self._postings or k <= 0:
            return []
        scores: dict[int, float] = {}
        total = len(self.chunks)
        average = self._avgdl or 1.0
        for term in content_terms(query):
            hits = self._postings.get(term)
            if not hits:
                continue
            document_frequency = len(hits)
            idf = math.log(1 + (total - document_frequency + 0.5) / (document_frequency + 0.5))
            for index, frequency in hits:
                length = self._doc_lengths[index] or 1
                denominator = frequency + self.BM25_K1 * (
                    1 - self.BM25_B + self.BM25_B * length / average
                )
                scores[index] = scores.get(index, 0.0) + idf * (
                    frequency * (self.BM25_K1 + 1) / denominator
                )
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [(index, score) for index, score in ranked[:k] if score > 0]

    def _cosine_at(self, query_embedding: np.ndarray, index_id: int) -> float:
        """Cosine of one stored chunk against an already normalised query."""
        vector = np.asarray(self.index.reconstruct(int(index_id)), dtype=np.float32)
        return float(np.dot(query_embedding[0], vector))

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Retrieve evidence chunks for a query, highest cosine first.

        ``score`` is cosine similarity in [-1, 1]. The dense top-k are always
        included. Up to ``k`` additional BM25 matches are included when they
        were not already in that dense list, with ``lexical_hit`` set, so a
        caller can admit a keyword match the embedding ranked lower. Fewer
        than ``k`` dense results are returned when the index is smaller.
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

        cosine_by_id: dict[int, float] = {}
        for score, index_id in zip(scores[0], indices[0]):
            if index_id < 0:
                continue
            cosine_by_id[int(index_id)] = float(score)

        lexical = self._lexical_top(query, k)
        lexical_score_by_id = {index_id: score for index_id, score in lexical}
        for index_id in lexical_score_by_id:
            if index_id not in cosine_by_id:
                cosine_by_id[index_id] = self._cosine_at(query_embedding, index_id)

        results = []
        for index_id, score in cosine_by_id.items():
            chunk = self.chunks[index_id]
            results.append(
                {
                    "score": score,
                    "lexical_score": lexical_score_by_id.get(index_id, 0.0),
                    "lexical_hit": index_id in lexical_score_by_id,
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "url": chunk["url"],
                    "chunk_id": chunk["chunk_id"],
                    **self.source_fields(chunk),
                }
            )
        results.sort(key=lambda row: row["score"], reverse=True)
        return results

    def source_fields(self, chunk: dict) -> dict:
        """Identifiers for one chunk; see the module docstring for each field."""
        raw_id = chunk.get("article_id")
        article_id = None if raw_id is None else str(raw_id)
        key, scope = article_key(chunk.get("url"), article_id, self.corpus_version)
        return {
            "article_id": article_id,
            "article_key": key,
            "article_key_scope": scope,
            "source_id": f"{key}#{text_sha256(chunk.get('text', ''))[:12]}",
            "index_ref": f"{self.index_version}:{article_id}:{chunk.get('chunk_id')}",
            "corpus_version": self.corpus_version,
            "index_version": self.index_version,
        }
