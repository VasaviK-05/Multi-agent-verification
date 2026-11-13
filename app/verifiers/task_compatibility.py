"""Task-population contracts for the four verifiers.

A population status describes the benchmark, not a single lucky item.
UNSUPPORTED means the verifier must not be treated as having verified the
answer. A direct arithmetic expression can still be checked when it matches
a deterministic rule, including when a caller mislabels that expression as
GSM8K. A GSM8K word problem that is not one explicit expression stays
unsupported.

This module does not load embedding models, the evidence index, or Ollama.
"""

from __future__ import annotations

from typing import Optional

from app.verifiers.confidence_verifier import parse_judgment_list
from app.verifiers.rule_verifier import RuleVerifier

POPULATIONS = ("direct_arithmetic", "gsm8k", "direct_facts", "hotpotqa", "fever")
VERIFIERS = ("semantic", "evidence", "rule", "confidence")

# Population-level declarations. VERIFIED means the implementation decides
# that population. PARTIALLY_VERIFIED means a real but limited path exists.
# UNSUPPORTED means a success result would be a false claim. UNKNOWN means
# the research configuration does not pin the inputs required to judge it.
POPULATION_SUPPORT = {
    "semantic": {
        "direct_arithmetic": "UNSUPPORTED",
        "gsm8k": "PARTIALLY_VERIFIED",
        "direct_facts": "PARTIALLY_VERIFIED",
        "hotpotqa": "PARTIALLY_VERIFIED",
        "fever": "UNKNOWN",
    },
    "evidence": {
        "direct_arithmetic": "UNSUPPORTED",
        "gsm8k": "UNSUPPORTED",
        "direct_facts": "PARTIALLY_VERIFIED",
        "hotpotqa": "PARTIALLY_VERIFIED",
        "fever": "UNSUPPORTED",
    },
    "rule": {
        "direct_arithmetic": "VERIFIED",
        "gsm8k": "UNSUPPORTED",
        "direct_facts": "PARTIALLY_VERIFIED",
        "hotpotqa": "UNSUPPORTED",
        "fever": "UNSUPPORTED",
    },
    "confidence": {
        "direct_arithmetic": "PARTIALLY_VERIFIED",
        "gsm8k": "PARTIALLY_VERIFIED",
        "direct_facts": "UNKNOWN",
        "hotpotqa": "UNKNOWN",
        "fever": "UNKNOWN",
    },
}

RETRIEVAL_GATE = 0.78


def population_support(verifier: str, population: str) -> str:
    if verifier not in POPULATION_SUPPORT or population not in POPULATIONS:
        raise ValueError(f"unknown verifier or population: {verifier!r}, {population!r}")
    return POPULATION_SUPPORT[verifier][population]


def _unsupported(reason: str) -> dict:
    return {
        "task_support": "UNSUPPORTED",
        "decision": "UNSURE",
        "passed": False,
        "score_is_correctness": False,
        "reason": reason,
    }


def enforce_task_support(verifier: str, population: str, passed: bool, decision: str) -> dict:
    """Downgrade a success claim when the population is unsupported."""
    support = population_support(verifier, population)
    if support == "UNSUPPORTED":
        return _unsupported(
            f"{verifier} does not verify the {population} population. "
            "A returned score is not a successful verification."
        )
    return {
        "task_support": support,
        "decision": decision,
        "passed": passed if support != "UNKNOWN" else False,
        "score_is_correctness": False,
        "reason": "Population support is limited or not established. The score is not correctness.",
    }


def rule_item(question: str, answer: str, population: str) -> dict:
    """Run the deterministic rule verifier and apply the population contract.

    Direct arithmetic is verified only when a factual arithmetic rule matches.
    Any other rule, including a structural format check, does not verify a
    factual population. GSM8K word problems that are not a single explicit
    expression stay unsupported even if some numbers appear in the text.
    """
    if population not in POPULATIONS:
        raise ValueError(population)
    result = RuleVerifier().verify(question, answer)
    metadata = result.metadata or {}
    rule = metadata.get("rule")
    arithmetic = isinstance(rule, str) and rule.startswith("arithmetic_")
    if population == "direct_arithmetic" and arithmetic:
        return {
            "task_support": "VERIFIED",
            "decision": metadata.get("decision"),
            "passed": result.passed,
            "score_is_correctness": True,
            "rule": rule,
            "reason": "A single explicit arithmetic expression was checked with exact Decimal arithmetic.",
        }
    if population == "gsm8k" and arithmetic:
        return {
            "task_support": "VERIFIED",
            "decision": metadata.get("decision"),
            "passed": result.passed,
            "score_is_correctness": True,
            "rule": rule,
            "reason": "The item is a single explicit expression, not a multi-step word problem. The GSM8K population remains unsupported.",
        }
    if population in {"direct_arithmetic", "gsm8k", "hotpotqa", "fever"}:
        return _unsupported(
            "No deterministic arithmetic rule matched. The answer was not treated as verified."
        )
    if rule == "unsupported":
        return _unsupported("No deterministic factual rule matched this direct-fact item.")
    factual = metadata.get("rule_kind") == "factual" and metadata.get("decision") in {"SUPPORT", "REJECT"}
    return {
        "task_support": "PARTIALLY_VERIFIED",
        "decision": metadata.get("decision"),
        "passed": result.passed if factual else False,
        "score_is_correctness": factual,
        "rule": rule,
        "reason": "Only the listed factual or structural patterns were checked. This is not general factual verification.",
    }


def semantic_contract(population: str, context: Optional[str]) -> dict:
    """Reference text is required. Similarity is not factual correctness."""
    support = population_support("semantic", population)
    if support == "UNSUPPORTED":
        return _unsupported("Semantic similarity does not verify arithmetic correctness.")
    if context is None or not str(context).strip() or parse_judgment_list(context) is not None:
        return _unsupported("Semantic verification requires reference text. Judgment labels are not a reference.")
    return {
        "task_support": support,
        "decision": "UNSURE",
        "passed": False,
        "score_is_correctness": False,
        "reason": "Reference text is present. A later cosine score measures resemblance, not factual correctness.",
    }


def evidence_contract(population: str, retrieval: Optional[dict] = None) -> dict:
    """Retrieval coverage is not a correctness decision.

    ``retrieval`` may report ``supporting_above_gate`` from a prior measurement.
    Missing evidence stays insufficient. This function does not invent documents.
    """
    support = population_support("evidence", population)
    if support == "UNSUPPORTED":
        return _unsupported(
            "The canonical research corpus does not establish evidence verification for this population."
        )
    above_gate = bool(retrieval and retrieval.get("supporting_above_gate") is True)
    if not above_gate:
        return {
            "task_support": "INSUFFICIENT_EVIDENCE",
            "decision": "UNSURE",
            "passed": False,
            "score_is_correctness": False,
            "reason": f"No supporting hit at cosine >= {RETRIEVAL_GATE}. Insufficiency is preserved.",
        }
    return {
        "task_support": "PARTIALLY_VERIFIED",
        "decision": "UNSURE",
        "passed": False,
        "score_is_correctness": False,
        "reason": "A supporting chunk cleared the retrieval gate. That is not a correctness verdict.",
    }


def confidence_contract(population: str) -> dict:
    """Agreement is not correctness. The research generator snapshot is unknown."""
    support = population_support("confidence", population)
    if support == "UNKNOWN":
        return {
            "task_support": "UNKNOWN",
            "decision": "UNSURE",
            "passed": False,
            "score_is_correctness": False,
            "reason": "No frozen generator snapshot is approved for this population. Agreement would not be correctness.",
        }
    return {
        "task_support": support,
        "decision": "UNSURE",
        "passed": False,
        "score_is_correctness": False,
        "reason": "Numeric agreement can be counted, but the generator model hash is UNKNOWN and the score is not correctness.",
    }
