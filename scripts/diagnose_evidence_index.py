import json
import os
from pathlib import Path

from app.verifiers.evidence_retriever import (
    EvidenceRetriever,
    default_corpus_path,
)

print("EVIDENCE_CORPUS_PATH:", os.getenv("EVIDENCE_CORPUS_PATH"))
print("Default corpus:", default_corpus_path())

corpora = [
    "data/articles_13083.json",
    "data/evidence_corpus.json",
    "data/test_evidence_corpus.json",
]

for corpus_path in corpora:
    path = Path(corpus_path)

    print(f"\n{'=' * 60}")
    print("Corpus:", path.resolve())
    print("Exists:", path.is_file())

    if not path.is_file():
        continue

    retriever = EvidenceRetriever(corpus_path=str(path))

    print("Selected index:", retriever.index_dir.resolve())
    print("Corpus SHA:", retriever.corpus_version)
    print("Index version:", retriever.index_version)
    print("Chunks loaded:", len(retriever.chunks))
    print("FAISS vectors:", retriever.index.ntotal)

    if retriever.manifest_path.exists():
        manifest = json.loads(
            retriever.manifest_path.read_text(encoding="utf-8")
        )
        print("Manifest:")
        print(json.dumps(manifest, indent=2))

    print("Sample titles:")
    print(sorted({c.get("title", "") for c in retriever.chunks})[:10])