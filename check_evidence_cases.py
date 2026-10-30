"""Retrieval-only check against the corpus in EVIDENCE_CORPUS_PATH.

Prints the chunks EvidenceRetriever actually returns. It does not run NLI.
``expect`` is a title fragment that this corpus is known to contain; None
means this file has no dedicated source article for that question.
"""

from app.verifiers.claim_generator import ClaimGenerator, factual_question
from app.verifiers.evidence_retriever import EvidenceRetriever

CASES = [
    ("France", "What is the capital of France?", "Paris", None),
    ("Romeo", "Who wrote Romeo and Juliet?", "William Shakespeare", None),
    (
        "UEFA winner",
        "Who won the 2010 UEFA Europa League final?",
        "Sevilla FC",
        "2010 UEFA Europa League final",
    ),
    (
        "Water",
        "At what temperature does water boil at sea level?",
        "100°C (212°F)",
        None,
    ),
    (
        "UEFA date",
        "What was the date of the 2010 UEFA Europa League final? Answer only in YYYY-MM-DD format.",
        "2010-05-19",
        "2010 UEFA Europa League final",
    ),
    (
        "UEFA multi-fact",
        "Compare the location, date, winner, final score, and extra-time outcome of the 2010 UEFA Europa League final.",
        "The 2010 UEFA Europa League final was played at the Volksparkstadion in Hamburg on 12 May 2010. "
        "Atlético Madrid defeated Fulham 2-1 after extra time.",
        "2010 UEFA Europa League final",
    ),
    (
        "Tocopilla",
        "What were the principal characteristics of the 2007 Tocopilla earthquake "
        "in terms of its location, magnitude, duration, aftershocks, and tsunami warning?",
        "The 2007 Tocopilla earthquake occurred in northern Chile on 14 November 2007. "
        "It had a magnitude of 7.7 and lasted approximately 3 minutes and 35 seconds. "
        "There were 17 aftershocks above magnitude 5.3, including one magnitude 7.1.",
        "2007 Tocopilla earthquake",
    ),
]

def show(text: str) -> str:
    """Keep titles printable in a Windows console."""
    return str(text).encode("cp1252", errors="replace").decode("cp1252")


retriever = EvidenceRetriever()
claims = ClaimGenerator()
print("corpus:", retriever.corpus_path)
print("chunks:", retriever.index.ntotal)

for name, question, answer, expect in CASES:
    print("\n===", name, "===")
    found = False
    for item in claims.generate_claims(question, answer):
        query = f"{factual_question(question)} {item['claim']}"
        hits = retriever.retrieve(query, k=5)
        print("query:", show(query))
        if not hits:
            print("  no hits")
            continue
        for rank, hit in enumerate(hits, start=1):
            mark = "keyword" if hit.get("lexical_hit") else "dense"
            print(f"  {rank}. {hit['score']:.3f}  {mark:7}  {show(hit['title'])}")
            if expect and expect.lower() in hit["title"].lower():
                found = True
    if expect:
        print("FOUND" if found else "MISSING", expect)
    else:
        print("no source article in this corpus; top titles above are the nearest chunks")
