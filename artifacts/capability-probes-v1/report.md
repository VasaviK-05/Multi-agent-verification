# Capability probes: exploratory diagnostics

Fixed 12 groups / 24 answers / 96 existing-verifier calls, at most 120 local generations. No policies were fitted, probabilities changed or reputations updated. This is not held-out evidence.

Earlier baseline pairs came from the selector count defaults and coverage/ranking fill, plus the execution floor. Every selected verifier still received the whole question, answer and context. Evidence internally splits some claims; that is not a cross-verifier component-binding protocol.

The flexible engine enumerates all eligible nonempty teams and checks actual informative contributions, coverage and thresholds. Routing and fitted policy selection are separate; none of these diagnostic results registers a new policy or expands the prototype allowlist.

The opt-in CapabilityProbeAnalyzer recognizes the exact Rule-supported word-difference template missed by the legacy analyzer. Existing atomic analysis is unchanged. Two explicit mixed templates retain both requirements and an unsupported component-binding requirement, so they fail closed instead of silently becoming only factual.

All weighting uses unchanged existing arithmetic/factual/semantic task-family history as a limited diagnostic scenario. It is not reliability calibration for new contrasts or wordings. Mixed inputs have no compatible history or policy and receive no fabricated team verdict. Semantic measures resemblance, not a logical-equivalence certificate.

## a-multiply

What is 37 * 19?

Reference: The product of 37 and 19 is 703.

Required checks: ['arithmetic']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Compare exact multiplication with generation agreement and reference resemblance.
Interface support: Supported binary Rule input; other verifiers may abstain or disagree.
Correct answer: 703
Deliberately incorrect answer: 693
Independent label provenance: "Independent Decimal integer multiplication: 37*19=703."
Legacy requirements: ['arithmetic']; opt-in requirements: ['arithmetic']; unsupported: [].

a-multiply-correct / semantic: directional; decision SUPPORT; score 0.8608709323075975; achieved []; informative under frozen family history 1; measured call 182.1052001323551 ms.

a-multiply-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 69.912200095132 ms.

a-multiply-correct / rule: directional; decision SUPPORT; score 1.0; achieved ['arithmetic']; informative under frozen family history 1; measured call 3.1720998231321573 ms.

a-multiply-correct / confidence: abstention; decision UNSURE; score 0.8; achieved []; informative under frozen family history 0; measured call 18872.44539987296 ms.

a-multiply-incorrect / semantic: directional; decision SUPPORT; score 0.8088431333701013; achieved []; informative under frozen family history 1; measured call 28.302700025960803 ms.

a-multiply-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 45.81829998642206 ms.

a-multiply-incorrect / rule: directional; decision REJECT; score 0.0; achieved ['arithmetic']; informative under frozen family history 1; measured call 0.13229995965957642 ms.

a-multiply-incorrect / confidence: abstention; decision UNSURE; score 1.0; achieved []; informative under frozen family history 0; measured call 11376.201800070703 ms.

## a-word-difference

What is the difference between 25 and 17?

Reference: Subtracting 17 from 25 yields 8.

Required checks: ['arithmetic']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Exercise wording accepted by Rule but missed by the existing analyzer; additional results cannot replace missing routing.
Interface support: Rule input supported; legacy analyzer requirements unknown; opt-in analyzer adds a versioned category.
Correct answer: 8
Deliberately incorrect answer: 42
Independent label provenance: "Independent integer subtraction; wrong answer is the sum, not the difference."
Legacy requirements: []; opt-in requirements: ['arithmetic']; unsupported: [].

a-word-difference-correct / semantic: directional; decision SUPPORT; score 0.7517677646079888; achieved []; informative under frozen family history 1; measured call 27.677200036123395 ms.

a-word-difference-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 42.50480001792312 ms.

a-word-difference-correct / rule: directional; decision SUPPORT; score 1.0; achieved ['arithmetic']; informative under frozen family history 1; measured call 2.0075999200344086 ms.

a-word-difference-correct / confidence: directional; decision SUPPORT; score 1.0; achieved []; informative under frozen family history 1; measured call 11865.342899924144 ms.

a-word-difference-incorrect / semantic: directional; decision SUPPORT; score 0.6840941804190346; achieved []; informative under frozen family history 1; measured call 46.84820002876222 ms.

a-word-difference-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 82.55400019697845 ms.

a-word-difference-incorrect / rule: directional; decision REJECT; score 0.0; achieved ['arithmetic']; informative under frozen family history 1; measured call 0.12529990635812283 ms.

a-word-difference-incorrect / confidence: directional; decision REJECT; score 1.0; achieved []; informative under frozen family history 1; measured call 11679.683999856934 ms.

## a-division

What is 17 / 4?

Reference: Seventeen divided by four equals 4.25.

Required checks: ['arithmetic']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Check exact arithmetic versus a nearby numeric distractor under the existing rounding policy.
Interface support: Supported binary Rule input; 4.2 is wrong even at its displayed precision (expected 4.3).
Correct answer: 4.25
Deliberately incorrect answer: 4.2
Independent label provenance: "Independent Decimal division and explicit half-up rounding check."
Legacy requirements: ['arithmetic']; opt-in requirements: ['arithmetic']; unsupported: [].

a-division-correct / semantic: directional; decision SUPPORT; score 0.791691011103241; achieved []; informative under frozen family history 1; measured call 30.31830000691116 ms.

a-division-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 71.98369991965592 ms.

a-division-correct / rule: directional; decision SUPPORT; score 1.0; achieved ['arithmetic']; informative under frozen family history 1; measured call 1.1076000519096851 ms.

a-division-correct / confidence: directional; decision SUPPORT; score 1.0; achieved []; informative under frozen family history 1; measured call 12367.711499799043 ms.

a-division-incorrect / semantic: directional; decision SUPPORT; score 0.7235375793034495; achieved []; informative under frozen family history 1; measured call 27.98729995265603 ms.

a-division-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 46.18619987741113 ms.

a-division-incorrect / rule: directional; decision REJECT; score 0.0; achieved ['arithmetic']; informative under frozen family history 1; measured call 0.19449996761977673 ms.

a-division-incorrect / confidence: directional; decision REJECT; score 1.0; achieved []; informative under frozen family history 1; measured call 11926.408600062132 ms.

## f-area

What is the area of Bahrain?

Reference: The area of Bahrain is 765 square kilometres.

Required checks: ['direct_fact']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast retrieval/NLI with similarity and generation agreement on a near-number or related-currency distractor.
Interface support: Existing factual interface; numeric facts do not imply arithmetic coverage.
Correct answer: The area of Bahrain is 765 square kilometres.
Deliberately incorrect answer: The area of Bahrain is 766 square kilometres.
Independent label provenance: {"iso": "BH", "kind": "area", "source_hashes": {"LICENSE": "a221a27af5e4ef5a9cecce097c718c28f1aaf7d368cb57c994aa447c68d9defc", "countries-revision.json": "102428d79a671fa4394dd487e75f8daf517fc388aa86793d8b4575a68c170ba7", "countries.json": "0d92fb23b43ae080bd439f5dc5d61a8845395fdd0af1479b433c59fe079bd6fd", "geonames-countryInfo.txt": "5c710efde90ee4cca15001c9f6a97ae7a74c7020b365504913ddc3afeb6d3671"}, "source_snapshot_truth": true, "value": 765}
Legacy requirements: ['direct_fact']; opt-in requirements: ['direct_fact']; unsupported: [].

f-area-correct / semantic: directional; decision SUPPORT; score 0.9656733595003932; achieved []; informative under frozen family history 0; measured call 75.76390006579459 ms.

f-area-correct / evidence: directional; decision SUPPORT; score 0.9929022192955017; achieved ['direct_fact']; informative under frozen family history 1; measured call 560.2984998840839 ms.

f-area-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 5.096399923786521 ms.

f-area-correct / confidence: abstention; decision UNSURE; score 0.8; achieved []; informative under frozen family history 0; measured call 13075.214899843559 ms.

f-area-incorrect / semantic: directional; decision SUPPORT; score 0.9564483897373305; achieved []; informative under frozen family history 0; measured call 58.76039993017912 ms.

f-area-incorrect / evidence: directional; decision REJECT; score 0.9769747257232666; achieved ['direct_fact']; informative under frozen family history 1; measured call 157.70350000821054 ms.

f-area-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.11819996871054173 ms.

f-area-incorrect / confidence: abstention; decision UNSURE; score 0.8; achieved []; informative under frozen family history 0; measured call 12948.28400015831 ms.

## f-population

What is the population of Belgium?

Reference: The population of Belgium is 11941781.

Required checks: ['direct_fact']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast retrieval/NLI with similarity and generation agreement on a near-number or related-currency distractor.
Interface support: Existing factual interface; numeric facts do not imply arithmetic coverage.
Correct answer: The population of Belgium is 11941781.
Deliberately incorrect answer: The population of Belgium is 11941718.
Independent label provenance: {"iso": "BE", "kind": "population", "source_hashes": {"LICENSE": "a221a27af5e4ef5a9cecce097c718c28f1aaf7d368cb57c994aa447c68d9defc", "countries-revision.json": "102428d79a671fa4394dd487e75f8daf517fc388aa86793d8b4575a68c170ba7", "countries.json": "0d92fb23b43ae080bd439f5dc5d61a8845395fdd0af1479b433c59fe079bd6fd", "geonames-countryInfo.txt": "5c710efde90ee4cca15001c9f6a97ae7a74c7020b365504913ddc3afeb6d3671"}, "source_snapshot_truth": true, "value": 11941781}
Legacy requirements: ['direct_fact']; opt-in requirements: ['direct_fact']; unsupported: [].

f-population-correct / semantic: directional; decision SUPPORT; score 0.9616148877440465; achieved []; informative under frozen family history 0; measured call 36.267900140956044 ms.

f-population-correct / evidence: directional; decision SUPPORT; score 0.9903382658958435; achieved ['direct_fact']; informative under frozen family history 1; measured call 168.51680004037917 ms.

f-population-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.7764999754726887 ms.

f-population-correct / confidence: abstention; decision UNSURE; score 1.0; achieved []; informative under frozen family history 0; measured call 13775.616300059482 ms.

f-population-incorrect / semantic: directional; decision SUPPORT; score 0.9512402081161948; achieved []; informative under frozen family history 0; measured call 39.83979998156428 ms.

f-population-incorrect / evidence: directional; decision REJECT; score 0.9908571839332581; achieved ['direct_fact']; informative under frozen family history 1; measured call 156.16569994017482 ms.

f-population-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.1276999246329069 ms.

f-population-incorrect / confidence: abstention; decision UNSURE; score 1.0; achieved []; informative under frozen family history 0; measured call 13542.723099933937 ms.

## f-currency

What is the currency of Cuba?

Reference: The currency of Cuba is the Cuban peso.

Required checks: ['direct_fact']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast retrieval/NLI with similarity and generation agreement on a near-number or related-currency distractor.
Interface support: Existing factual interface; numeric facts do not imply arithmetic coverage.
Correct answer: The currency of Cuba is the Cuban peso.
Deliberately incorrect answer: The currency of Cuba is the Mexican peso.
Independent label provenance: {"iso": "CU", "kind": "currency", "source_hashes": {"LICENSE": "a221a27af5e4ef5a9cecce097c718c28f1aaf7d368cb57c994aa447c68d9defc", "countries-revision.json": "102428d79a671fa4394dd487e75f8daf517fc388aa86793d8b4575a68c170ba7", "countries.json": "0d92fb23b43ae080bd439f5dc5d61a8845395fdd0af1479b433c59fe079bd6fd", "geonames-countryInfo.txt": "5c710efde90ee4cca15001c9f6a97ae7a74c7020b365504913ddc3afeb6d3671"}, "source_snapshot_truth": true, "value": "Cuban peso"}
Legacy requirements: ['direct_fact']; opt-in requirements: ['direct_fact']; unsupported: [].

f-currency-correct / semantic: directional; decision SUPPORT; score 0.9303758750265613; achieved []; informative under frozen family history 0; measured call 36.234499886631966 ms.

f-currency-correct / evidence: directional; decision SUPPORT; score 0.9954079985618591; achieved ['direct_fact']; informative under frozen family history 1; measured call 170.8533000200987 ms.

f-currency-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.13810000382363796 ms.

f-currency-correct / confidence: directional; decision SUPPORT; score 1.0; achieved []; informative under frozen family history 1; measured call 14009.516099933535 ms.

f-currency-incorrect / semantic: directional; decision SUPPORT; score 0.9266930375125461; achieved []; informative under frozen family history 0; measured call 31.465600011870265 ms.

f-currency-incorrect / evidence: directional; decision REJECT; score 0.9992812275886536; achieved ['direct_fact']; informative under frozen family history 1; measured call 214.95010005310178 ms.

f-currency-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.09510014206171036 ms.

f-currency-incorrect / confidence: abstention; decision UNSURE; score 1.0; achieved []; informative under frozen family history 0; measured call 14234.585699858144 ms.

## s-number

Paraphrase this reference: Nora placed four amber tokens in the blue box.

Reference: Nora placed four amber tokens in the blue box.

Required checks: ['semantic_comparison']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast logical equivalence with cosine resemblance and generation/NLI agreement.
Interface support: Semantic input/measurement supported; similarity contract is not a logical-equivalence certificate. Synthetic frames are not added to the retrieval corpus.
Correct answer: Four amber tokens were placed in the blue box by Nora.
Deliberately incorrect answer: Nora placed five amber tokens in the blue box.
Independent label provenance: {"method": "independent predicate/argument/count/negation reasoning", "proof": "Exact count preservation versus four-to-five change."}
Legacy requirements: ['semantic_comparison']; opt-in requirements: ['semantic_comparison']; unsupported: [].

s-number-correct / semantic: directional; decision SUPPORT; score 0.9367262919047104; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 39.7558999247849 ms.

s-number-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 29.703699983656406 ms.

s-number-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.14819996431469917 ms.

s-number-correct / confidence: directional; decision SUPPORT; score 1.0; achieved []; informative under frozen family history 1; measured call 15961.844499921426 ms.

s-number-incorrect / semantic: directional; decision SUPPORT; score 0.93092015962996; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 31.07649995945394 ms.

s-number-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 51.905399886891246 ms.

s-number-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.11039990931749344 ms.

s-number-incorrect / confidence: abstention; decision UNSURE; score 1.0; achieved []; informative under frozen family history 0; measured call 15528.167699929327 ms.

## s-negation

Paraphrase this reference: Owen did not open the red gate.

Reference: Owen did not open the red gate.

Required checks: ['semantic_comparison']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast logical equivalence with cosine resemblance and generation/NLI agreement.
Interface support: Semantic input/measurement supported; similarity contract is not a logical-equivalence certificate. Synthetic frames are not added to the retrieval corpus.
Correct answer: The red gate was not opened by Owen.
Deliberately incorrect answer: Owen opened the red gate.
Independent label provenance: {"method": "independent predicate/argument/count/negation reasoning", "proof": "Explicit negation preserved versus reversed."}
Legacy requirements: ['semantic_comparison']; opt-in requirements: ['semantic_comparison']; unsupported: [].

s-negation-correct / semantic: directional; decision SUPPORT; score 0.8220675544500978; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 57.968500070273876 ms.

s-negation-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 32.60620008222759 ms.

s-negation-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.08850009180605412 ms.

s-negation-correct / confidence: directional; decision SUPPORT; score 0.6; achieved []; informative under frozen family history 1; measured call 14850.155899999663 ms.

s-negation-incorrect / semantic: directional; decision SUPPORT; score 0.8173035103342556; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 51.097899908199906 ms.

s-negation-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 47.05239995382726 ms.

s-negation-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.10240008123219013 ms.

s-negation-incorrect / confidence: abstention; decision UNSURE; score 1.0; achieved []; informative under frozen family history 0; measured call 14508.812099928036 ms.

## s-roles

Paraphrase this reference: Mira lent a book to Theo.

Reference: Mira lent a book to Theo.

Required checks: ['semantic_comparison']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast logical equivalence with cosine resemblance and generation/NLI agreement.
Interface support: Semantic input/measurement supported; similarity contract is not a logical-equivalence certificate. Synthetic frames are not added to the retrieval corpus.
Correct answer: Theo borrowed a book from Mira.
Deliberately incorrect answer: Theo lent a book to Mira.
Independent label provenance: {"method": "independent predicate/argument/count/negation reasoning", "proof": "Lender/borrower roles preserved versus reversed."}
Legacy requirements: ['semantic_comparison']; opt-in requirements: ['semantic_comparison']; unsupported: [].

s-roles-correct / semantic: directional; decision SUPPORT; score 0.9082583474158291; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 41.29420011304319 ms.

s-roles-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 45.06999999284744 ms.

s-roles-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.07830001413822174 ms.

s-roles-correct / confidence: directional; decision SUPPORT; score 1.0; achieved []; informative under frozen family history 1; measured call 14419.480700045824 ms.

s-roles-incorrect / semantic: directional; decision SUPPORT; score 0.927489771888306; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 51.43750016577542 ms.

s-roles-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 35.489900037646294 ms.

s-roles-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.13739988207817078 ms.

s-roles-incorrect / confidence: directional; decision REJECT; score 1.0; achieved []; informative under frozen family history 1; measured call 14520.425299881026 ms.

## s-spatial

Paraphrase this reference: The cedar crate is to the left of the oak crate.

Reference: The cedar crate is to the left of the oak crate.

Required checks: ['semantic_comparison']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Contrast logical equivalence with cosine resemblance and generation/NLI agreement.
Interface support: Semantic input/measurement supported; similarity contract is not a logical-equivalence certificate. Synthetic frames are not added to the retrieval corpus.
Correct answer: The oak crate is to the right of the cedar crate.
Deliberately incorrect answer: The cedar crate is to the right of the oak crate.
Independent label provenance: {"method": "independent predicate/argument/count/negation reasoning", "proof": "Left/right inverse relation preserved versus contradicted."}
Legacy requirements: ['semantic_comparison']; opt-in requirements: ['semantic_comparison']; unsupported: [].

s-spatial-correct / semantic: directional; decision SUPPORT; score 0.9281350465610243; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 43.12809999100864 ms.

s-spatial-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 30.373399844393134 ms.

s-spatial-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.085500068962574 ms.

s-spatial-correct / confidence: directional; decision SUPPORT; score 1.0; achieved []; informative under frozen family history 1; measured call 16231.03650007397 ms.

s-spatial-incorrect / semantic: directional; decision SUPPORT; score 0.9287209998146546; achieved ['semantic_comparison']; informative under frozen family history 0; measured call 36.26710013486445 ms.

s-spatial-incorrect / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 30.549800023436546 ms.

s-spatial-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history 0; measured call 0.10859989561140537 ms.

s-spatial-incorrect / confidence: directional; decision REJECT; score 1.0; achieved []; informative under frozen family history 1; measured call 16035.787899978459 ms.

## m-area

What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values.

Reference: The area of Bahrain is 765 square kilometres.

Required checks: ['direct_fact', 'arithmetic']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Requires retrieving the base fact and checking the derived result; merely selecting two names cannot bind components.
Interface support: Diagnostic compound only; whole-question Rule matching and component binding are unsupported.
Correct answer: The area of Bahrain is 765 square kilometres. Adding 10 gives 775 square kilometres.
Deliberately incorrect answer: The area of Bahrain is 765 square kilometres. Adding 10 gives 774 square kilometres.
Independent label provenance: {"calculation": "765+10=775", "fact": {"iso": "BH", "kind": "area", "source_hashes": {"LICENSE": "a221a27af5e4ef5a9cecce097c718c28f1aaf7d368cb57c994aa447c68d9defc", "countries-revision.json": "102428d79a671fa4394dd487e75f8daf517fc388aa86793d8b4575a68c170ba7", "countries.json": "0d92fb23b43ae080bd439f5dc5d61a8845395fdd0af1479b433c59fe079bd6fd", "geonames-countryInfo.txt": "5c710efde90ee4cca15001c9f6a97ae7a74c7020b365504913ddc3afeb6d3671"}, "source_snapshot_truth": true, "value": 765}, "negative": "Correct base fact, incorrect derived sum."}
Legacy requirements: []; opt-in requirements: ['direct_fact', 'arithmetic']; unsupported: ['compound_component_binding_v1'].

m-area-correct / semantic: directional; decision SUPPORT; score 0.7924816329732183; achieved []; informative under frozen family history None; measured call 45.87629996240139 ms.

m-area-correct / evidence: directional; decision REJECT; score 0.0032712738029658794; achieved []; informative under frozen family history None; measured call 300.6128999404609 ms.

m-area-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history None; measured call 0.11730007827281952 ms.

m-area-correct / confidence: abstention; decision UNSURE; score 0.8; achieved []; informative under frozen family history None; measured call 20839.570900192484 ms.

m-area-incorrect / semantic: directional; decision SUPPORT; score 0.7986371048919052; achieved []; informative under frozen family history None; measured call 38.7081999797374 ms.

m-area-incorrect / evidence: directional; decision REJECT; score 0.0018009401392191648; achieved []; informative under frozen family history None; measured call 288.2245001383126 ms.

m-area-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history None; measured call 0.08279993198812008 ms.

m-area-incorrect / confidence: directional; decision SUPPORT; score 0.8; achieved []; informative under frozen family history None; measured call 19248.76119988039 ms.

## m-population

What is the population of Belgium, and what is that population plus 1000? Give both values.

Reference: The population of Belgium is 11941781.

Required checks: ['direct_fact', 'arithmetic']. Eligible by prerequisites: ['semantic', 'evidence', 'rule', 'confidence'].
Why extra checking might help: Distinguish a wrong retrieved base fact from an internally consistent calculation on that wrong base.
Interface support: Diagnostic compound only; a fact-looking prefix must not drop the arithmetic obligation.
Correct answer: The population of Belgium is 11941781. Adding 1000 gives 11942781.
Deliberately incorrect answer: The population of Belgium is 11941718. Adding 1000 gives 11942718.
Independent label provenance: {"calculation": "11941781+1000=11942781", "fact": {"iso": "BE", "kind": "population", "source_hashes": {"LICENSE": "a221a27af5e4ef5a9cecce097c718c28f1aaf7d368cb57c994aa447c68d9defc", "countries-revision.json": "102428d79a671fa4394dd487e75f8daf517fc388aa86793d8b4575a68c170ba7", "countries.json": "0d92fb23b43ae080bd439f5dc5d61a8845395fdd0af1479b433c59fe079bd6fd", "geonames-countryInfo.txt": "5c710efde90ee4cca15001c9f6a97ae7a74c7020b365504913ddc3afeb6d3671"}, "source_snapshot_truth": true, "value": 11941781}, "negative": "Wrong base fact; addition internally correct for the supplied wrong base, but whole answer incorrect."}
Legacy requirements: ['direct_fact']; opt-in requirements: ['direct_fact', 'arithmetic']; unsupported: ['compound_component_binding_v1'].

m-population-correct / semantic: directional; decision SUPPORT; score 0.7177876010785732; achieved []; informative under frozen family history None; measured call 45.00989988446236 ms.

m-population-correct / evidence: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history None; measured call 295.3097999561578 ms.

m-population-correct / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history None; measured call 0.13449997641146183 ms.

m-population-correct / confidence: directional; decision SUPPORT; score 0.8; achieved []; informative under frozen family history None; measured call 21913.26899989508 ms.

m-population-incorrect / semantic: directional; decision SUPPORT; score 0.7146971400080201; achieved []; informative under frozen family history None; measured call 40.73389992117882 ms.

m-population-incorrect / evidence: directional; decision REJECT; score 0.9908571839332581; achieved ['direct_fact']; informative under frozen family history None; measured call 351.09749995172024 ms.

m-population-incorrect / rule: abstention; decision UNSURE; score 0.0; achieved []; informative under frozen family history None; measured call 0.16300007700920105 ms.

m-population-incorrect / confidence: directional; decision SUPPORT; score 0.6; achieved []; informative under frozen family history None; measured call 21616.66060006246 ms.

## Team summaries

All eligible singles/pairs/triples/quads and both aggregations are retained. Counts below are over six arithmetic, six factual or eight reference examples. Multiple context identities in a family are descriptive pooling only, not one compatible policy or a payoff fit. Historical team costs are estimates, not measured deployment latency.

arithmetic / rule / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 9.678209995036013 ms.

arithmetic / rule / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 9.678209995036013 ms.

arithmetic / confidence,rule / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21137.283848738298 ms.

arithmetic / confidence,rule / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21137.283848738298 ms.

arithmetic / evidence,rule / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 91.13092127081472 ms.

arithmetic / evidence,rule / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 91.13092127081472 ms.

arithmetic / rule,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 49.27691500342917 ms.

arithmetic / rule,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 49.27691500342917 ms.

arithmetic / confidence,evidence,rule / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21218.736560014077 ms.

arithmetic / confidence,evidence,rule / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21218.736560014077 ms.

arithmetic / confidence,rule,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21176.88255374669 ms.

arithmetic / confidence,rule,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21176.88255374669 ms.

arithmetic / evidence,rule,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 130.72962627920788 ms.

arithmetic / evidence,rule,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 130.72962627920788 ms.

arithmetic / confidence,evidence,rule,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21258.33526502247 ms.

arithmetic / confidence,evidence,rule,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 21258.33526502247 ms.

factual / evidence / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 188.79894875281025 ms.

factual / evidence / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 188.79894875281025 ms.

factual / confidence,evidence / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15921.25526748423 ms.

factual / confidence,evidence / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15921.25526748423 ms.

factual / evidence,rule / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 188.90355375187937 ms.

factual / evidence,rule / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 188.90355375187937 ms.

factual / evidence,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 232.48554126475938 ms.

factual / evidence,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 232.48554126475938 ms.

factual / confidence,evidence,rule / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15921.3598724833 ms.

factual / confidence,evidence,rule / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15921.3598724833 ms.

factual / confidence,evidence,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15964.94185999618 ms.

factual / confidence,evidence,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15964.94185999618 ms.

factual / evidence,rule,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 232.5901462638285 ms.

factual / evidence,rule,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 232.5901462638285 ms.

factual / confidence,evidence,rule,semantic / reputation_weighted: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15965.046464995248 ms.

factual / confidence,evidence,rule,semantic / dependency_group: coverage 1.0, false accept 0, false reject 0, uncertainty 0, loss 0.0, selective risk 0.0, estimated cost 15965.046464995248 ms.

semantic / semantic / reputation_weighted: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 42.32344499905594 ms.

semantic / semantic / dependency_group: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 42.32344499905594 ms.

semantic / confidence,semantic / reputation_weighted: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15820.463388747885 ms.

semantic / confidence,semantic / dependency_group: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15820.463388747885 ms.

semantic / evidence,semantic / reputation_weighted: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 74.17498749564402 ms.

semantic / evidence,semantic / dependency_group: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 74.17498749564402 ms.

semantic / rule,semantic / reputation_weighted: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 42.43273748434149 ms.

semantic / rule,semantic / dependency_group: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 42.43273748434149 ms.

semantic / confidence,evidence,semantic / reputation_weighted: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15852.314931244473 ms.

semantic / confidence,evidence,semantic / dependency_group: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15852.314931244473 ms.

semantic / confidence,rule,semantic / reputation_weighted: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15820.57268123317 ms.

semantic / confidence,rule,semantic / dependency_group: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15820.57268123317 ms.

semantic / evidence,rule,semantic / reputation_weighted: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 74.28427998092957 ms.

semantic / evidence,rule,semantic / dependency_group: coverage 0.0, false accept 0, false reject 0, uncertainty 8, loss 0.19999999999999998, selective risk None, estimated cost 74.28427998092957 ms.

semantic / confidence,evidence,rule,semantic / reputation_weighted: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15852.424223729759 ms.

semantic / confidence,evidence,rule,semantic / dependency_group: coverage 0.75, false accept 0, false reject 0, uncertainty 2, loss 0.05, selective risk 0.0, estimated cost 15852.424223729759 ms.

## Adding one verifier

These exhaustive post-hoc comparisons are diagnostics, not an oracle available to routing. Counts: {'same_loss': 432, 'helps': 48}.

helps:
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "reputation_weighted", "before": "uncertain", "change": "helps", "child": ["confidence", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "dependency_group", "before": "uncertain", "change": "helps", "child": ["confidence", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "reputation_weighted", "before": "uncertain", "change": "helps", "child": ["confidence", "evidence", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["evidence", "semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "dependency_group", "before": "uncertain", "change": "helps", "child": ["confidence", "evidence", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["evidence", "semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "reputation_weighted", "before": "uncertain", "change": "helps", "child": ["confidence", "rule", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["rule", "semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "dependency_group", "before": "uncertain", "change": "helps", "child": ["confidence", "rule", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["rule", "semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "reputation_weighted", "before": "uncertain", "change": "helps", "child": ["confidence", "evidence", "rule", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["evidence", "rule", "semantic"]}
- {"added": "confidence", "additional_estimated_cost_ms": 15778.139943748829, "after": "passed", "aggregation": "dependency_group", "before": "uncertain", "change": "helps", "child": ["confidence", "evidence", "rule", "semantic"], "example_id": "s-number-correct", "family": "semantic", "loss_after": 0.0, "loss_before": 0.2, "note": "Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.", "parent": ["evidence", "rule", "semantic"]}

hurts:
No observed cases.

## Compound support

{"achieved_unbound_report_capabilities": [], "enumeration_status": "no_feasible_strategy", "example_id": "m-area-correct", "expected_union_teams": [["evidence", "rule"], ["evidence", "rule", "semantic"], ["confidence", "evidence", "rule"], ["confidence", "evidence", "rule", "semantic"]], "limitation": "Expected union is not compound coverage. No component binding or mixed history/policy; no compound acceptance or decision-loss comparison is manufactured.", "missing_actual_checks": ["arithmetic", "direct_fact"], "public_status": "uncertain", "reasons": ["unsupported_requirements"], "required": ["direct_fact", "arithmetic"]}

{"achieved_unbound_report_capabilities": [], "enumeration_status": "no_feasible_strategy", "example_id": "m-area-incorrect", "expected_union_teams": [["evidence", "rule"], ["evidence", "rule", "semantic"], ["confidence", "evidence", "rule"], ["confidence", "evidence", "rule", "semantic"]], "limitation": "Expected union is not compound coverage. No component binding or mixed history/policy; no compound acceptance or decision-loss comparison is manufactured.", "missing_actual_checks": ["arithmetic", "direct_fact"], "public_status": "uncertain", "reasons": ["unsupported_requirements"], "required": ["direct_fact", "arithmetic"]}

{"achieved_unbound_report_capabilities": [], "enumeration_status": "no_feasible_strategy", "example_id": "m-population-correct", "expected_union_teams": [["evidence", "rule"], ["evidence", "rule", "semantic"], ["confidence", "evidence", "rule"], ["confidence", "evidence", "rule", "semantic"]], "limitation": "Expected union is not compound coverage. No component binding or mixed history/policy; no compound acceptance or decision-loss comparison is manufactured.", "missing_actual_checks": ["arithmetic", "direct_fact"], "public_status": "uncertain", "reasons": ["unsupported_requirements"], "required": ["direct_fact", "arithmetic"]}

{"achieved_unbound_report_capabilities": ["direct_fact"], "enumeration_status": "no_feasible_strategy", "example_id": "m-population-incorrect", "expected_union_teams": [["evidence", "rule"], ["evidence", "rule", "semantic"], ["confidence", "evidence", "rule"], ["confidence", "evidence", "rule", "semantic"]], "limitation": "Expected union is not compound coverage. No component binding or mixed history/policy; no compound acceptance or decision-loss comparison is manufactured.", "missing_actual_checks": ["arithmetic"], "public_status": "uncertain", "reasons": ["unsupported_requirements"], "required": ["direct_fact", "arithmetic"]}

## Limits and next step

Abstention and missing/unsupported coverage remain uncertainty. No report identities or verifier algorithms were changed. No independent failure paths are inferred from different names; the original shared-unknown dependency registry is retained. No new attack campaign was run.

See raw collection/recordings.json and individual-findings.json for all findings, including unsuccessful probes. Team-outcomes.json retains contributors, achieved/missing checks and reasons; all-addition-comparisons.json includes negative and unchanged outcomes.

Any future policy fit needs fresh grouped history/development/test partitions after question-only categories, component contracts and baselines are predeclared. Do not reuse the completed held-out outcomes or these explored probes as a new untouched test set. A legitimate fit may still select only singletons or report infeasibility.
