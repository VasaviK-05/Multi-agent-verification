
import json
import time

from app.verifiers.rule_verifier import RuleVerifier
from app.verifiers.semantic_verifier import SemanticVerifier
from app.verifiers.confidence_verifier import ConfidenceVerifier
from app.verifiers.evidence_verifier import EvidenceVerifier


def show_result(name, result, elapsed):
    print(f"\n{name}")
    print("Decision:", (result.metadata or {}).get("decision"))
    print("Passed:", result.passed)
    print("Score:", result.score)
    print("Latency:", round(elapsed * 1000, 2), "ms")
    print("Reasoning:", result.reasoning[:250])


def run_test(name, verifier, question, answer, context=None):
    start = time.perf_counter()
    result = verifier.verify(question, answer, context)
    elapsed = time.perf_counter() - start
    show_result(name, result, elapsed)


def main():
    print("Initializing verifiers...")

    rule = RuleVerifier()
    semantic = SemanticVerifier()

    # Explicit judgments are used only to test the verifier interface.
    # They are NOT benchmark ground truth or model-generated confidence.
    confidence = ConfidenceVerifier(
        judgment_provider=None
    )

    evidence = EvidenceVerifier()

    print("\nAll four verifiers initialized.")

    run_test(
        "Rule",
        rule,
        "What is 25 + 17?",
        "42"
    )

    run_test(
        "Semantic",
        semantic,
        "Who wrote Romeo and Juliet?",
        "William Shakespeare",
        "William Shakespeare wrote Romeo and Juliet."
    )

    run_test(
        "Confidence",
        confidence,
        "Who wrote Romeo and Juliet?",
        "William Shakespeare",
        judgments_context := None
    ) if False else print(
        "\nConfidence: use explicit judgments in the direct test below."
    )

    result = confidence.verify(
        "Who wrote Romeo and Juliet?",
        "William Shakespeare",
        judgments=["support", "support", "support", "reject"]
    )
    print("\nConfidence")
    print("Decision:", result.metadata.get("decision"))
    print("Majority:", result.metadata.get("majority_label"))
    print("Score:", result.score)

    run_test(
        "Evidence",
        evidence,
        "Who wrote Romeo and Juliet?",
        "William Shakespeare"
    )


if __name__ == "__main__":
    main()
