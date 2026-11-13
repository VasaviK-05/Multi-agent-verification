"""Identifiers shared by the research-readiness checks.

Hashes below are the recorded bytes of artifacts this package validates.
The checkers recompute file hashes and treat a mismatch as a blocker.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CANONICAL_CORPUS = "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"
CANONICAL_CORPUS_SHA256 = "f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b"
CANONICAL_INDEX_DIR = "evaluation/artifacts/person1/development_evidence_corpus_v1/evidence_index/corpus"
CANONICAL_INDEX_ID = "idx-c1dc6980912b"
INDEX_MANIFEST_SHA256 = "2a7ce5a45101e26c73bd4a8c3255d4c743166b24e9339f4d8f5fe983a9ab8521"
INDEX_CHUNKS_SHA256 = "1d207b208905a3ce3a85c4c567ecc5cc8b24106d43964ebda046a7da51963bc7"
INDEX_FAISS_SHA256 = "037e4923b2c69c86b5f7fb83c8589c6b89ed7fe714d7cbb70581a7700aacb7d8"

ELIGIBILITY_MANIFEST = "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json"
ELIGIBILITY_BODY_SHA256 = "f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d"
ELIGIBLE_CANDIDATES = 744
ELIGIBLE_GROUPS = 372
GSM8K_GROUPS = 187
HOTPOTQA_GROUPS = 185

FINAL_TEST_MANIFEST = "evaluation/datasets/final_test_research_v1_eval_v2/manifest.json"
FINAL_TEST_CONTENT_HASH = "e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee"

HISTORICAL_CORPORA = {
    "data/evidence_corpus.json": "668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5",
    "data/articles_13083.json": "b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8",
}
