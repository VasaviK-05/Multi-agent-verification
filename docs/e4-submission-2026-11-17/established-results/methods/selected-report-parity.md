# Exact selected-report runtime finalization parity

The two [paired records](../data/parity/) compare original saved API outputs with replay of the same selected Rule report payloads through the existing pure finalize_decision() interface. Frozen artifact context, contract, selected strategy and validation ID were preserved. No verifier algorithm was re-executed.

| Case | Retained verifier decision | Original final | Replayed final | Exact comparison |
|---|---|---|---|---|
| Correct arithmetic | SUPPORT | passed | passed | Match |
| Incorrect arithmetic | REJECT | failed | failed | Match |

Result: **2 exact matches, 0 mismatches**. Comparisons include the complete numerical decision (votes/weights and aggregation), public status, contributors, required/achieved/unresolved coverage, reasons, ordered execution states and estimated attempted cost. Unchanged report payloads and their hashes are retained. The comparison unit is selected Rule reports and pure runtime finalization. [Arithmetic policy](../data/configuration/arithmetic-policy.json) preserves the exact frozen object used by the comparison.
