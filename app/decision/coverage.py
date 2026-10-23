"""Pure achieved-output contracts shared by baseline orchestration and offline replay."""

from app.models.schemas import VerificationResult
from app.decision.vote_normalization import is_abstention, vote_confidence

ARITHMETIC_RULES = frozenset({
    "arithmetic_addition", "arithmetic_subtraction",
    "arithmetic_multiplication", "arithmetic_division",
})


def factual_capabilities(result: VerificationResult) -> set[str]:
    """Recognize current factual output contracts, regardless of checker name.

    Rule expected/actual fields are optional on legitimate invalid-answer
    rejections. Evidence requires assessed claims and matching evidence rows;
    an identity or bare decision is never a coverage certificate.
    """
    metadata = result.metadata or {}
    if is_abstention(result) or vote_confidence(result) == 0:
        return set()
    decision = metadata.get("decision")
    if decision not in {"SUPPORT", "REJECT"}:
        return set()
    capabilities = set()
    rule = metadata.get("rule")
    if (metadata.get("rule_kind") == "factual"
            and isinstance(rule, str) and rule in ARITHMETIC_RULES):
        capabilities.add("arithmetic")
    label = "entailment" if decision == "SUPPORT" else "contradiction"
    rows = metadata.get("supporting" if result.passed else "contradicting")
    opposite = metadata.get("contradicting" if result.passed else "supporting")
    claims = metadata.get("claim_decisions")
    if (metadata.get("nli_label") == label and metadata.get("unsure_reason") is None
            and isinstance(rows, list) and rows
            and any(isinstance(row, dict) and row.get("nli_label") == label for row in rows)
            and isinstance(claims, list) and claims):
        # Support requires every claim; rejection needs one decisive claim.
        directions = [c.get("decision") for c in claims if isinstance(c, dict)]
        if ((decision == "SUPPORT" and len(directions) == len(claims)
                and all(d == "SUPPORT" for d in directions) and not opposite)
                or (decision == "REJECT" and "REJECT" in directions)):
            capabilities.add("direct_fact")
    return capabilities
