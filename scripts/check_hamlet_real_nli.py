import json

from app.verifiers.evidence_verifier import EvidenceVerifier
from tests.test_evidence_verifier import FakeRetriever, chunk

passage = "Shakespeare wrote Hamlet."

# Fake retrieval only; NLI is the real default model.
retriever = FakeRetriever([
    chunk("Hamlet", passage, 0.9)
])

verifier = EvidenceVerifier(retriever=retriever)

result = verifier.verify(
    "Who wrote Hamlet?",
    "Shakespeare",
)

metadata = result.metadata

print("\n=== REAL NLI HAMLET DIAGNOSTIC ===")
print("NLI model:", metadata.get("nli_model"))
print("Question: Who wrote Hamlet?")
print("Answer: Shakespeare")
print("Retrieved passage:", passage)
print("Final decision:", metadata.get("decision"))
print("Passed:", result.passed)
print("NLI label:", metadata.get("nli_label"))
print("Unsure reason:", metadata.get("unsure_reason"))

print("\n=== EVALUATED EVIDENCE (REACHED NLI) ===")
print(json.dumps(
    metadata.get("evaluated_evidence", []),
    indent=2,
    ensure_ascii=False,
))

print("\n=== DISCARDED EVIDENCE ===")
print(json.dumps(
    metadata.get("discarded_evidence", []),
    indent=2,
    ensure_ascii=False,
))

print("\n=== CLAIM DECISIONS ===")
print(json.dumps(
    metadata.get("claim_decisions", []),
    indent=2,
    ensure_ascii=False,
))

evaluated = metadata.get("evaluated_evidence", [])
hamlet_evaluated = any(
    "Shakespeare wrote Hamlet" in str(row.get("relevant_evidence", ""))
    for row in evaluated
)

print("\n=== REGRESSION CHECK ===")
print("Hamlet passage reached NLI:", hamlet_evaluated)
print("Evidence evaluated:", bool(evaluated))
print("Evidence discarded:", len(metadata.get("discarded_evidence", [])))
