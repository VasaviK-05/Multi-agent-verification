# Factual development report

Engineering development evidence only. The fitted artifact always abstains and is not a useful operational policy.

Artifact: `238adc94fa3d6d81f60740d4cb585c52befa1748ea2ca1ee7aa2e169cf464236`
Budget: 12955.553737469 summed attempt ms; resource weight: 7.71869748113e-06 loss/ms.

## Every strategy

- confidence, evidence; reputation_weighted; probability 0; estimated cost 12903.808043734 ms.
- confidence, evidence; dependency_group; probability 0; estimated cost 12903.808043734 ms.
- evidence, rule; reputation_weighted; probability 1; estimated cost 181.689941246 ms.
- evidence, rule; dependency_group; probability 0; estimated cost 181.689941246 ms.
- evidence, semantic; reputation_weighted; probability 0; estimated cost 233.181544984 ms.
- evidence, semantic; dependency_group; probability 0; estimated cost 233.181544984 ms.
- confidence, evidence, rule; reputation_weighted; probability 0; estimated cost 12903.935088732 ms.
- confidence, evidence, rule; dependency_group; probability 0; estimated cost 12903.935088732 ms.
- confidence, evidence, semantic; reputation_weighted; probability 0; estimated cost 12955.426692471 ms.
- confidence, evidence, semantic; dependency_group; probability 0; estimated cost 12955.426692471 ms.
- evidence, rule, semantic; reputation_weighted; probability 0; estimated cost 233.308589982 ms.
- evidence, rule, semantic; dependency_group; probability 0; estimated cost 233.308589982 ms.
- confidence, evidence, rule, semantic; reputation_weighted; probability 0; estimated cost 12955.553737469 ms.
- confidence, evidence, rule, semantic; dependency_group; probability 0; estimated cost 12955.553737469 ms.

## Fitted-policy scenarios

- clean: validation loss 0.2; false accept 0.0/40; false reject 0.0/40; uncertainty 100.000%; coverage 0.000%; estimated cost 181.689941246 ms; cost-inclusive objective 0.201402409692.
- forced_support: validation loss 0.2; false accept 0.0/40; false reject 0.0/40; uncertainty 100.000%; coverage 0.000%; estimated cost 181.689941246 ms; cost-inclusive objective 0.201402409692.
- forced_rejection: validation loss 0.2; false accept 0.0/40; false reject 0.0/40; uncertainty 100.000%; coverage 0.000%; estimated cost 181.689941246 ms; cost-inclusive objective 0.201402409692.
- confidence_inflation: validation loss 0.2; false accept 0.0/40; false reject 0.0/40; uncertainty 100.000%; coverage 0.000%; estimated cost 181.689941246 ms; cost-inclusive objective 0.201402409692.
- suppression: validation loss 0.2; false accept 0.0/40; false reject 0.0/40; uncertainty 100.000%; coverage 0.000%; estimated cost 181.689941246 ms; cost-inclusive objective 0.201402409692.

## History and contributor weights

[
  {
    "verifier_name": "semantic",
    "domain": "general",
    "alpha": 21.0,
    "beta": 21.0,
    "successes": 20,
    "failures": 20,
    "observation_count": 40,
    "posterior_mean": 0.5,
    "posterior_variance": 0.005813953488372093,
    "cold_start": false,
    "log_odds_weight": 0.0
  },
  {
    "verifier_name": "evidence",
    "domain": "general",
    "alpha": 41.0,
    "beta": 1.0,
    "successes": 40,
    "failures": 0,
    "observation_count": 40,
    "posterior_mean": 0.9761904761904762,
    "posterior_variance": 0.0005405262880345942,
    "cold_start": false,
    "log_odds_weight": 3.7135720667043066
  },
  {
    "verifier_name": "rule",
    "domain": "general",
    "alpha": 1.0,
    "beta": 1.0,
    "successes": 0,
    "failures": 0,
    "observation_count": 0,
    "posterior_mean": 0.5,
    "posterior_variance": 0.08333333333333333,
    "cold_start": true,
    "log_odds_weight": 0.0
  },
  {
    "verifier_name": "confidence",
    "domain": "general",
    "alpha": 41.0,
    "beta": 1.0,
    "successes": 40,
    "failures": 0,
    "observation_count": 40,
    "posterior_mean": 0.9761904761904762,
    "posterior_variance": 0.0005405262880345942,
    "cold_start": false,
    "log_odds_weight": 3.7135720667043066
  }
]

## Compatible recorded baselines

Recorded complete teams and identical public guards; not equivalent to production feedback or early stopping

{
  "captured_greedy": {
    "strategy_id": "521d922d91e2367835123c62acfae9d81b982483fd5d4ef79bb63ec38e1704be",
    "verifiers": [
      "confidence",
      "evidence"
    ],
    "aggregation": "reputation_weighted",
    "estimated_cost": 12903.80804373417,
    "probability": 0.0,
    "scenarios": [
      {
        "attack_id": "f6db1d60fc8e415c1096942bad534779d546f9d4c58ea8c082c9b1825a22e782",
        "metrics": {
          "examples": 40,
          "correct_accept": 19.0,
          "correct_reject": 19.0,
          "false_accept": 0.0,
          "false_reject": 0.0,
          "uncertain": 2.0,
          "unresolved": 0.0,
          "decision_coverage": 0.95,
          "selective_risk": 0.0,
          "estimated_resource_cost": 12903.80804373417,
          "mean_loss": 0.10960059064410971
        },
        "validation_loss": 0.01
      },
      {
        "attack_id": "a69c629a2584dc8681efde073abe5c0a14c7b8088ab9e7d89bab7f246b5c4245",
        "metrics": {
          "examples": 40,
          "correct_accept": 19.0,
          "correct_reject": 0.0,
          "false_accept": 20.0,
          "false_reject": 0.0,
          "uncertain": 1.0,
          "unresolved": 0.0,
          "decision_coverage": 0.975,
          "selective_risk": 0.5128205128205128,
          "estimated_resource_cost": 12903.80804373417,
          "mean_loss": 0.6046005906441098
        },
        "validation_loss": 0.505
      },
      {
        "attack_id": "25bf123c7e8d7f003621ae90e5d6f6ea1420a388d2ef8ada6408c7d7cb7ce469",
        "metrics": {
          "examples": 40,
          "correct_accept": 0.0,
          "correct_reject": 20.0,
          "false_accept": 0.0,
          "false_reject": 19.0,
          "uncertain": 1.0,
          "unresolved": 0.0,
          "decision_coverage": 0.975,
          "selective_risk": 0.48717948717948717,
          "estimated_resource_cost": 12903.80804373417,
          "mean_loss": 0.5796005906441097
        },
        "validation_loss": 0.48
      },
      {
        "attack_id": "4b28ec0c6fcd5c21a7d0625b9aeb6675c20f70afec214787f7d0cec1e2fd1f01",
        "metrics": {
          "examples": 40,
          "correct_accept": 19.0,
          "correct_reject": 19.0,
          "false_accept": 0.0,
          "false_reject": 0.0,
          "uncertain": 2.0,
          "unresolved": 0.0,
          "decision_coverage": 0.95,
          "selective_risk": 0.0,
          "estimated_resource_cost": 12903.80804373417,
          "mean_loss": 0.10960059064410971
        },
        "validation_loss": 0.01
      },
      {
        "attack_id": "068f66d9b1c88d601073ca13144be8968c5e5cad17427c6a53fe89c5ae7a38ad",
        "metrics": {
          "examples": 40,
          "correct_accept": 0.0,
          "correct_reject": 0.0,
          "false_accept": 0.0,
          "false_reject": 0.0,
          "uncertain": 40.0,
          "unresolved": 40.0,
          "decision_coverage": 0.0,
          "selective_risk": null,
          "estimated_resource_cost": 12903.80804373417,
          "mean_loss": 0.2996005906441097
        },
        "validation_loss": 0.2
      }
    ]
  },
  "uniform_feasible": [
    {
      "attack_id": "f6db1d60fc8e415c1096942bad534779d546f9d4c58ea8c082c9b1825a22e782",
      "metrics": {
        "examples": 40,
        "correct_accept": 13.857142857142827,
        "correct_reject": 13.714285714285685,
        "false_accept": 0.0,
        "false_reject": 0.0,
        "uncertain": 12.428571428571404,
        "unresolved": 0.0,
        "decision_coverage": 0.6892857142857128,
        "selective_risk": 0.0,
        "estimated_resource_cost": 7480.986234088361,
        "mean_loss": 0.11988632674425637
      },
      "validation_loss": 0.06214285714285702
    },
    {
      "attack_id": "a69c629a2584dc8681efde073abe5c0a14c7b8088ab9e7d89bab7f246b5c4245",
      "metrics": {
        "examples": 40,
        "correct_accept": 13.857142857142827,
        "correct_reject": 0.0,
        "false_accept": 14.285714285714255,
        "false_reject": 0.0,
        "uncertain": 11.857142857142835,
        "unresolved": 0.0,
        "decision_coverage": 0.7035714285714271,
        "selective_risk": 0.5076142131979695,
        "estimated_resource_cost": 7480.986234088361,
        "mean_loss": 0.47417204102997057
      },
      "validation_loss": 0.4164285714285706
    },
    {
      "attack_id": "25bf123c7e8d7f003621ae90e5d6f6ea1420a388d2ef8ada6408c7d7cb7ce469",
      "metrics": {
        "examples": 40,
        "correct_accept": 0.0,
        "correct_reject": 14.285714285714255,
        "false_accept": 0.0,
        "false_reject": 13.857142857142827,
        "uncertain": 11.857142857142835,
        "unresolved": 0.0,
        "decision_coverage": 0.7035714285714271,
        "selective_risk": 0.4923857868020305,
        "estimated_resource_cost": 7480.986234088361,
        "mean_loss": 0.4634577553156849
      },
      "validation_loss": 0.4057142857142849
    },
    {
      "attack_id": "4b28ec0c6fcd5c21a7d0625b9aeb6675c20f70afec214787f7d0cec1e2fd1f01",
      "metrics": {
        "examples": 40,
        "correct_accept": 13.857142857142827,
        "correct_reject": 13.714285714285685,
        "false_accept": 0.0,
        "false_reject": 0.0,
        "uncertain": 12.428571428571404,
        "unresolved": 0.0,
        "decision_coverage": 0.6892857142857128,
        "selective_risk": 0.0,
        "estimated_resource_cost": 7480.986234088361,
        "mean_loss": 0.11988632674425637
      },
      "validation_loss": 0.06214285714285702
    },
    {
      "attack_id": "068f66d9b1c88d601073ca13144be8968c5e5cad17427c6a53fe89c5ae7a38ad",
      "metrics": {
        "examples": 40,
        "correct_accept": 0.0,
        "correct_reject": 0.0,
        "false_accept": 0.0,
        "false_reject": 0.0,
        "uncertain": 40.00000000000007,
        "unresolved": 40.00000000000007,
        "decision_coverage": 0.0,
        "selective_risk": null,
        "estimated_resource_cost": 7480.986234088361,
        "mean_loss": 0.2577434696013992
      },
      "validation_loss": 0.20000000000000034
    }
  ]
}

## Representative correct and incorrect decisions

These retained history/development labels remain private/local. No final-test labels or outcomes were opened.

### AL-correct

What is the capital of Albania?
The capital of Albania is Tirana.
Independent correct label: True

Raw reports:
```json
[
  {
    "verifier_name": "confidence",
    "state": "directional",
    "report": {
      "verifier_name": "confidence",
      "score": 1.0,
      "passed": true,
      "reasoning": "Majority judgment: support. Agreement: 5/5. Confidence: 1.0000.",
      "metadata": {
        "agreement_count": 5,
        "claim": "The capital of Albania is Tirana.",
        "decision": "SUPPORT",
        "generator_model": "llama3.2:3b",
        "judgment_counts": {
          "support": 5
        },
        "judgment_source": "self_consistency",
        "judgments": [
          "support",
          "support",
          "support",
          "support",
          "support"
        ],
        "latency_breakdown_ms": {
          "labeling": 0.15,
          "sampling": 12252.29
        },
        "latency_ms": 12252.5,
        "majority_label": "support",
        "method": "self_consistency",
        "n_samples": 5,
        "samples": [
          {
            "label": "support",
            "method": "string_match",
            "sample": "Tirana."
          },
          {
            "label": "support",
            "method": "string_match",
            "sample": "Tirana."
          },
          {
            "label": "support",
            "method": "string_match",
            "sample": "Tirana."
          },
          {
            "label": "support",
            "method": "string_match",
            "sample": "Tirana."
          },
          {
            "label": "support",
            "method": "string_match",
            "sample": "Tirana."
          }
        ],
        "score_meaning": "Agreement fraction among the judgments (majority count / total). With the default provider the judgments are N independent regenerations of the answer labelled against the candidate answer. A consistency signal, not accuracy and not a probability of correctness: a model can be consistently wrong.",
        "stable_answer": true,
        "temperature": 0.8,
        "total_judgments": 5
      }
    }
  },
  {
    "verifier_name": "evidence",
    "state": "directional",
    "report": {
      "verifier_name": "evidence",
      "score": 0.9961258769035339,
      "passed": true,
      "reasoning": "NLI result: entailment. Retrieved evidence entails the claim. Evidence: Albania. Claim: The capital of Albania is Tirana. NLI confidence: 0.9961.",
      "metadata": {
        "best_retrieval_score": 0.958746612071991,
        "candidate_pipeline": [
          {
            "article_id": "AL",
            "article_key": "url:https://www.geonames.org/countries/AL/",
            "article_key_scope": "global",
            "chunk_id": 33,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:AL:33",
            "nli_executed": true,
            "passed_on_topic": true,
            "passed_select_relevant": true,
            "retrieval_score": 0.958746612071991,
            "source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "title": "Albania"
          },
          {
            "article_id": "FI",
            "article_key": "url:https://www.geonames.org/countries/FI/",
            "article_key_scope": "global",
            "chunk_id": 13,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:FI:13",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": false,
            "retrieval_score": 0.5252426862716675,
            "source_id": "url:https://www.geonames.org/countries/FI/#72300184967c",
            "title": "Finland"
          },
          {
            "article_id": "GR",
            "article_key": "url:https://www.geonames.org/countries/GR/",
            "article_key_scope": "global",
            "chunk_id": 1,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": "off_subject",
            "index_ref": "idx-caf1ed53307b:GR:1",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": true,
            "retrieval_score": 0.5187010765075684,
            "source_id": "url:https://www.geonames.org/countries/GR/#82834eb7e07e",
            "title": "Greece"
          },
          {
            "article_id": "IT",
            "article_key": "url:https://www.geonames.org/countries/IT/",
            "article_key_scope": "global",
            "chunk_id": 41,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:IT:41",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": false,
            "retrieval_score": 0.5154618620872498,
            "source_id": "url:https://www.geonames.org/countries/IT/#6262e19362c7",
            "title": "Italy"
          },
          {
            "article_id": "HU",
            "article_key": "url:https://www.geonames.org/countries/HU/",
            "article_key_scope": "global",
            "chunk_id": 26,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:HU:26",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": false,
            "retrieval_score": 0.4945682883262634,
            "source_id": "url:https://www.geonames.org/countries/HU/#917bb042aa3a",
            "title": "Hungary"
          },
          {
            "article_id": "CY",
            "article_key": "url:https://www.geonames.org/countries/CY/",
            "article_key_scope": "global",
            "chunk_id": 0,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": "off_subject",
            "index_ref": "idx-caf1ed53307b:CY:0",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": true,
            "retrieval_score": 0.43168196082115173,
            "source_id": "url:https://www.geonames.org/countries/CY/#06da230423d6",
            "title": "Cyprus"
          }
        ],
        "claim_decisions": [
          {
            "best_retrieval_score": 0.958746612071991,
            "claim": "The capital of Albania is Tirana.",
            "claim_id": "claim-0",
            "claim_index": 0,
            "confidence": 0.9961258769035339,
            "deciding_source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "decision": "SUPPORT",
            "evidence_refs": {
              "contradicting": [],
              "discarded": [
                "url:https://www.geonames.org/countries/GR/#82834eb7e07e",
                "url:https://www.geonames.org/countries/CY/#06da230423d6"
              ],
              "evaluated": [
                "url:https://www.geonames.org/countries/AL/#602e38d656d6"
              ],
              "ignored_contradictions": [],
              "ignored_support": [],
              "supporting": [
                "url:https://www.geonames.org/countries/AL/#602e38d656d6"
              ]
            },
            "hypothesis": "The capital of Albania is Tirana.",
            "template": "statement",
            "unsure_reason": null
          }
        ],
        "claims": [
          "The capital of Albania is Tirana."
        ],
        "contradicting": [],
        "corpus_version": "sha256:e7f747f05bcc5d46e401e3f6e1c89edc4b7b171db5b509c73621504253000630",
        "deciding_claim_id": "claim-0",
        "decision": "SUPPORT",
        "diagnostic_code": null,
        "discarded_evidence": [
          {
            "about_subject": false,
            "article_covers_event": false,
            "article_id": "GR",
            "article_key": "url:https://www.geonames.org/countries/GR/",
            "article_key_scope": "global",
            "chunk_id": 1,
            "claim_id": "claim-0",
            "claim_index": 0,
            "condition_consistent": true,
            "discard_code": "off_subject",
            "eligibility_basis": null,
            "entity_consistent": true,
            "event_consistent": true,
            "index_ref": "idx-caf1ed53307b:GR:1",
            "missing_anchor_terms": [
              "albania"
            ],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "reason": "article title is about a different subject than the question",
            "retrieval_score": 0.5187010765075684,
            "source_id": "url:https://www.geonames.org/countries/GR/#82834eb7e07e",
            "title": "Greece",
            "title_covers_event": false,
            "topic_coverage": 0.0,
            "url": "https://www.geonames.org/countries/GR/"
          },
          {
            "about_subject": false,
            "article_covers_event": false,
            "article_id": "CY",
            "article_key": "url:https://www.geonames.org/countries/CY/",
            "article_key_scope": "global",
            "chunk_id": 0,
            "claim_id": "claim-0",
            "claim_index": 0,
            "condition_consistent": true,
            "discard_code": "off_subject",
            "eligibility_basis": null,
            "entity_consistent": true,
            "event_consistent": true,
            "index_ref": "idx-caf1ed53307b:CY:0",
            "missing_anchor_terms": [
              "albania"
            ],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "reason": "article title is about a different subject than the question",
            "retrieval_score": 0.43168196082115173,
            "source_id": "url:https://www.geonames.org/countries/CY/#06da230423d6",
            "title": "Cyprus",
            "title_covers_event": false,
            "topic_coverage": 0.0,
            "url": "https://www.geonames.org/countries/CY/"
          }
        ],
        "evaluated_evidence": [
          {
            "about_subject": true,
            "article_covers_event": true,
            "article_id": "AL",
            "article_key": "url:https://www.geonames.org/countries/AL/",
            "article_key_scope": "global",
            "chunk_id": 33,
            "claim_id": "claim-0",
            "claim_index": 0,
            "claim_names_in_premise": true,
            "condition_consistent": true,
            "discard_code": "candidate_retained_for_nli",
            "eligibility_basis": "lexical_subject",
            "entity_consistent": true,
            "event_consistent": true,
            "fact_score": 3,
            "index_ref": "idx-caf1ed53307b:AL:33",
            "match_score": 2,
            "missing_anchor_terms": [],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "nli_label": "entailment",
            "nli_output_shape": "list[dict]",
            "nli_score": 0.9961258769035339,
            "office_holder_consistent": true,
            "premise_windows": [
              {
                "fact_score": 3,
                "nli_label": "entailment",
                "premise": "The capital of Albania is Tirana.",
                "probabilities": {
                  "contradiction": 0.0003329598985146731,
                  "entailment": 0.9961258769035339,
                  "neutral": 0.0035411606077104807
                },
                "title_dependent": false,
                "token_count": 17,
                "value_relation": "none"
              }
            ],
            "probabilities": {
              "contradiction": 0.0003329598985146731,
              "entailment": 0.9961258769035339,
              "neutral": 0.0035411606077104807
            },
            "quantity_kinds": [],
            "quantity_scope_aligned": true,
            "relation_aligned": true,
            "relevant_evidence": "The capital of Albania is Tirana.",
            "retrieval_score": 0.958746612071991,
            "source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "title": "Albania",
            "title_covers_event": false,
            "topic_coverage": 1.0,
            "url": "https://www.geonames.org/countries/AL/",
            "value_relation": "none"
          }
        ],
        "evidence_chunk_id": 33,
        "evidence_source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
        "evidence_title": "Albania",
        "ignored_contradictions": [],
        "ignored_support": [],
        "index_version": "idx-caf1ed53307b",
        "latency_breakdown_ms": {
          "nli": 415.68,
          "retrieval": 43.38,
          "total": 461.12
        },
        "latency_ms": 461.12,
        "max_premise_windows": 3,
        "min_nli_score": 0.5,
        "min_retrieval_score": 0.45,
        "min_topic_coverage": 0.5,
        "nli_label": "entailment",
        "nli_model": "cross-encoder/nli-deberta-v3-small",
        "nli_output_shape": "list[dict]",
        "retrieval_margin": 0.15,
        "retrieval_score": 0.958746612071991,
        "retrieved_counts": [
          {
            "claim_id": "claim-0",
            "claim_index": 0,
            "retrieved_count": 6
          }
        ],
        "score_meaning": "NLI probability of the label that decided the result (entailment for SUPPORT, contradiction for REJECT) on the deciding evidence chunk; 0 for UNSURE. A class probability from one model, not a calibrated probability that the answer is correct.",
        "supporting": [
          {
            "article_id": "AL",
            "article_key": "url:https://www.geonames.org/countries/AL/",
            "article_key_scope": "global",
            "chunk_id": 33,
            "claim_id": "claim-0",
            "claim_index": 0,
            "excerpt": "The capital of Albania is Tirana.",
            "index_ref": "idx-caf1ed53307b:AL:33",
            "nli_label": "entailment",
            "nli_score": 0.9961258769035339,
            "retrieval_score": 0.958746612071991,
            "source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "title": "Albania",
            "topic_coverage": 1.0,
            "url": "https://www.geonames.org/countries/AL/"
          }
        ],
        "thresholds_calibrated": false,
        "top_k": 3,
        "topic_margin": 0.3,
        "unchecked_claims": [],
        "unsure_reason": null
      }
    }
  },
  {
    "verifier_name": "rule",
    "state": "abstention",
    "report": {
      "verifier_name": "rule",
      "score": 0.0,
      "passed": false,
      "reasoning": "No supported deterministic rule matched the question.",
      "metadata": {
        "decision": "UNSURE",
        "latency_ms": 0.03,
        "rule": "unsupported",
        "rule_kind": null,
        "score_meaning": "Deterministic rule outcome bit: 1 when the check passed, 0 when it failed. Not a probability."
      }
    }
  },
  {
    "verifier_name": "semantic",
    "state": "directional",
    "report": {
      "verifier_name": "semantic",
      "score": 0.9357280066075385,
      "passed": true,
      "reasoning": "Semantic similarity score: 0.9357. Support threshold: 0.50; reject threshold: 0.30. Compared text is semantically close to the reference.",
      "metadata": {
        "compared_text": "What is the capital of Albania? The capital of Albania is Tirana.",
        "comparison_method": "question_answer_vs_context",
        "decision": "SUPPORT",
        "latency_ms": 80.5,
        "model": "all-MiniLM-L6-v2",
        "raw_similarity": 0.9357280066075385,
        "reject_threshold": 0.3,
        "score_meaning": "Cosine similarity between the compared text and the reference, clipped to [0, 1]. Measures resemblance of meaning, not factual correctness; not a probability and not calibrated.",
        "support_threshold": 0.5,
        "threshold": 0.5,
        "thresholds_calibrated": false
      }
    }
  }
]
```

Aggregation: reputation_weighted; numerical passed at 0.996125876904; public uncertain; contributors 1; required ['direct_fact']; achieved ['direct_fact']; reasons ['minimum_contributors'].
```json
{
  "aggregation": "log_odds",
  "aggregation_id": "reputation_weighted",
  "aggregation_version": "log_odds_v1",
  "dependency_assumptions": [],
  "dependency_configuration_id": null,
  "dependency_version": null,
  "domain": "general",
  "fallback": null,
  "groups": [],
  "lower_cut": -0.55,
  "missing_reports": [],
  "raw_score": 0.9961258769035339,
  "reputation_snapshot_id": "0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3",
  "score": 0.996126,
  "status": "passed",
  "team": [
    "evidence",
    "rule"
  ],
  "threshold": 0.55,
  "upper_cut": 0.55,
  "validation_id": "factual-capitals42-v1-development-AL-correct",
  "votes": [
    {
      "abstained": false,
      "confidence": 0.9961258769035339,
      "contribution": 3.699185231390296,
      "failure_group_id": null,
      "included": true,
      "inclusion_reason": "included",
      "normalized_strength": 0.9961258769035339,
      "passed": true,
      "reliability_strength": 0.9523809523809523,
      "reputation": 0.9761904761904762,
      "validation_id": "factual-capitals42-v1-development-AL-correct",
      "verifier_name": "evidence",
      "weight": 3.7135720667043066
    },
    {
      "abstained": true,
      "confidence": 0.0,
      "contribution": 0.0,
      "failure_group_id": null,
      "included": false,
      "inclusion_reason": "abstention",
      "normalized_strength": null,
      "passed": false,
      "reliability_strength": 0.0,
      "reputation": 0.5,
      "validation_id": "factual-capitals42-v1-development-AL-correct",
      "verifier_name": "rule",
      "weight": 0.0
    }
  ]
}
```

Aggregation: dependency_group; numerical passed at 0.996125876904; public uncertain; contributors 1; required ['direct_fact']; achieved ['direct_fact']; reasons ['minimum_contributors'].
```json
{
  "aggregation": "dependency_group",
  "aggregation_id": "dependency_group",
  "aggregation_version": "groups_v1",
  "dependency_assumptions": [
    "configured compromise pathways; conservative connected components",
    "unresolved verifiers share one unknown compromise pathway",
    "observed provenance is audit-only and never rewrites this registry"
  ],
  "dependency_configuration_id": "4ca2f113fd7b9ae042812ec16b0d5acc33eb4949018596936e66e652e3b13a1d",
  "dependency_version": "observed-shared-models-and-unresolved-v1",
  "domain": "general",
  "fallback": null,
  "groups": [
    {
      "active_members": [
        "evidence"
      ],
      "contribution": 0.9486913113366989,
      "fallback": null,
      "group_id": "cd406da454f8dbac024fd3ded624db5b0b9cb47a6297882e75553de387c5f374",
      "influence": 0.9523809523809523,
      "reliability_sum": 0.9523809523809523,
      "score": 0.9961258769035339
    }
  ],
  "lower_cut": -0.55,
  "missing_reports": [],
  "raw_score": 0.9961258769035339,
  "reputation_snapshot_id": "0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3",
  "score": 0.996126,
  "status": "passed",
  "team": [
    "evidence",
    "rule"
  ],
  "threshold": 0.55,
  "upper_cut": 0.55,
  "validation_id": "factual-capitals42-v1-development-AL-correct",
  "votes": [
    {
      "abstained": false,
      "confidence": 0.9961258769035339,
      "contribution": 0.9486913113366989,
      "failure_group_id": "cd406da454f8dbac024fd3ded624db5b0b9cb47a6297882e75553de387c5f374",
      "included": true,
      "inclusion_reason": "included",
      "normalized_strength": 0.9961258769035339,
      "passed": true,
      "reliability_strength": 0.9523809523809523,
      "reputation": 0.9761904761904762,
      "validation_id": "factual-capitals42-v1-development-AL-correct",
      "verifier_name": "evidence",
      "weight": 0.9523809523809523
    },
    {
      "abstained": true,
      "confidence": 0.0,
      "contribution": 0.0,
      "failure_group_id": "cd406da454f8dbac024fd3ded624db5b0b9cb47a6297882e75553de387c5f374",
      "included": false,
      "inclusion_reason": "abstention",
      "normalized_strength": null,
      "passed": false,
      "reliability_strength": 0.0,
      "reputation": 0.5,
      "validation_id": "factual-capitals42-v1-development-AL-correct",
      "verifier_name": "rule",
      "weight": 0.0
    }
  ]
}
```

### AL-incorrect

What is the capital of Albania?
The capital of Albania is Phnom Penh.
Independent correct label: False

Raw reports:
```json
[
  {
    "verifier_name": "confidence",
    "state": "directional",
    "report": {
      "verifier_name": "confidence",
      "score": 1.0,
      "passed": false,
      "reasoning": "Majority judgment: reject. Agreement: 5/5. Confidence: 1.0000.",
      "metadata": {
        "agreement_count": 5,
        "claim": "The capital of Albania is Phnom Penh.",
        "decision": "REJECT",
        "generator_model": "llama3.2:3b",
        "judgment_counts": {
          "reject": 5
        },
        "judgment_source": "self_consistency",
        "judgments": [
          "reject",
          "reject",
          "reject",
          "reject",
          "reject"
        ],
        "latency_breakdown_ms": {
          "labeling": 523.49,
          "sampling": 11997.22
        },
        "latency_ms": 12520.78,
        "majority_label": "reject",
        "method": "self_consistency",
        "n_samples": 5,
        "samples": [
          {
            "label": "reject",
            "method": "nli",
            "nli": {
              "contradiction": 0.9998899698257446,
              "entailment": 1.9222066839574836e-05,
              "neutral": 9.086769568966702e-05
            },
            "premise": "The capital of Albania is Tirana.",
            "sample": "Tirana."
          },
          {
            "label": "reject",
            "method": "nli",
            "nli": {
              "contradiction": 0.9998899698257446,
              "entailment": 1.9222066839574836e-05,
              "neutral": 9.086769568966702e-05
            },
            "premise": "The capital of Albania is Tirana.",
            "sample": "Tirana."
          },
          {
            "label": "reject",
            "method": "nli",
            "nli": {
              "contradiction": 0.9998899698257446,
              "entailment": 1.9222066839574836e-05,
              "neutral": 9.086769568966702e-05
            },
            "premise": "The capital of Albania is Tirana.",
            "sample": "Tirana."
          },
          {
            "label": "reject",
            "method": "nli",
            "nli": {
              "contradiction": 0.9998899698257446,
              "entailment": 1.9222066839574836e-05,
              "neutral": 9.086769568966702e-05
            },
            "premise": "The capital of Albania is Tirana.",
            "sample": "Tirana."
          },
          {
            "label": "reject",
            "method": "nli",
            "nli": {
              "contradiction": 0.9998899698257446,
              "entailment": 1.9222066839574836e-05,
              "neutral": 9.086769568966702e-05
            },
            "premise": "The capital of Albania is Tirana.",
            "sample": "Tirana."
          }
        ],
        "score_meaning": "Agreement fraction among the judgments (majority count / total). With the default provider the judgments are N independent regenerations of the answer labelled against the candidate answer. A consistency signal, not accuracy and not a probability of correctness: a model can be consistently wrong.",
        "stable_answer": true,
        "temperature": 0.8,
        "total_judgments": 5
      }
    }
  },
  {
    "verifier_name": "evidence",
    "state": "directional",
    "report": {
      "verifier_name": "evidence",
      "score": 0.9998899698257446,
      "passed": false,
      "reasoning": "NLI result: contradiction. Retrieved evidence contradicts the claim. Evidence: Albania. Claim: The capital of Albania is Phnom Penh. NLI confidence: 0.9999.",
      "metadata": {
        "best_retrieval_score": 0.8648569583892822,
        "candidate_pipeline": [
          {
            "article_id": "AL",
            "article_key": "url:https://www.geonames.org/countries/AL/",
            "article_key_scope": "global",
            "chunk_id": 33,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:AL:33",
            "nli_executed": true,
            "passed_on_topic": true,
            "passed_select_relevant": true,
            "retrieval_score": 0.8648569583892822,
            "source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "title": "Albania"
          },
          {
            "article_id": "KH",
            "article_key": "url:https://www.geonames.org/countries/KH/",
            "article_key_scope": "global",
            "chunk_id": 34,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": "off_subject",
            "index_ref": "idx-caf1ed53307b:KH:34",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": true,
            "retrieval_score": 0.6353930830955505,
            "source_id": "url:https://www.geonames.org/countries/KH/#bb072723c8d2",
            "title": "Cambodia"
          },
          {
            "article_id": "FI",
            "article_key": "url:https://www.geonames.org/countries/FI/",
            "article_key_scope": "global",
            "chunk_id": 13,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:FI:13",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": false,
            "retrieval_score": 0.5252426862716675,
            "source_id": "url:https://www.geonames.org/countries/FI/#72300184967c",
            "title": "Finland"
          },
          {
            "article_id": "IT",
            "article_key": "url:https://www.geonames.org/countries/IT/",
            "article_key_scope": "global",
            "chunk_id": 41,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": null,
            "index_ref": "idx-caf1ed53307b:IT:41",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": false,
            "retrieval_score": 0.5154618620872498,
            "source_id": "url:https://www.geonames.org/countries/IT/#6262e19362c7",
            "title": "Italy"
          },
          {
            "article_id": "GR",
            "article_key": "url:https://www.geonames.org/countries/GR/",
            "article_key_scope": "global",
            "chunk_id": 1,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": "off_subject",
            "index_ref": "idx-caf1ed53307b:GR:1",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": true,
            "retrieval_score": 0.5026056170463562,
            "source_id": "url:https://www.geonames.org/countries/GR/#82834eb7e07e",
            "title": "Greece"
          },
          {
            "article_id": "CY",
            "article_key": "url:https://www.geonames.org/countries/CY/",
            "article_key_scope": "global",
            "chunk_id": 0,
            "claim_id": "claim-0",
            "claim_index": 0,
            "discard_code": "off_subject",
            "index_ref": "idx-caf1ed53307b:CY:0",
            "nli_executed": false,
            "passed_on_topic": false,
            "passed_select_relevant": true,
            "retrieval_score": 0.43168196082115173,
            "source_id": "url:https://www.geonames.org/countries/CY/#06da230423d6",
            "title": "Cyprus"
          }
        ],
        "claim_decisions": [
          {
            "best_retrieval_score": 0.8648569583892822,
            "claim": "The capital of Albania is Phnom Penh.",
            "claim_id": "claim-0",
            "claim_index": 0,
            "confidence": 0.9998899698257446,
            "deciding_source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "decision": "REJECT",
            "evidence_refs": {
              "contradicting": [
                "url:https://www.geonames.org/countries/AL/#602e38d656d6"
              ],
              "discarded": [
                "url:https://www.geonames.org/countries/KH/#bb072723c8d2",
                "url:https://www.geonames.org/countries/GR/#82834eb7e07e",
                "url:https://www.geonames.org/countries/CY/#06da230423d6"
              ],
              "evaluated": [
                "url:https://www.geonames.org/countries/AL/#602e38d656d6"
              ],
              "ignored_contradictions": [],
              "ignored_support": [],
              "supporting": []
            },
            "hypothesis": "The capital of Albania is Phnom Penh.",
            "template": "statement",
            "unsure_reason": null
          }
        ],
        "claims": [
          "The capital of Albania is Phnom Penh."
        ],
        "contradicting": [
          {
            "article_id": "AL",
            "article_key": "url:https://www.geonames.org/countries/AL/",
            "article_key_scope": "global",
            "chunk_id": 33,
            "claim_id": "claim-0",
            "claim_index": 0,
            "excerpt": "The capital of Albania is Tirana.",
            "index_ref": "idx-caf1ed53307b:AL:33",
            "nli_label": "contradiction",
            "nli_score": 0.9998899698257446,
            "retrieval_score": 0.8648569583892822,
            "source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "title": "Albania",
            "topic_coverage": 1.0,
            "url": "https://www.geonames.org/countries/AL/"
          }
        ],
        "corpus_version": "sha256:e7f747f05bcc5d46e401e3f6e1c89edc4b7b171db5b509c73621504253000630",
        "deciding_claim_id": "claim-0",
        "decision": "REJECT",
        "diagnostic_code": null,
        "discarded_evidence": [
          {
            "about_subject": false,
            "article_covers_event": false,
            "article_id": "KH",
            "article_key": "url:https://www.geonames.org/countries/KH/",
            "article_key_scope": "global",
            "chunk_id": 34,
            "claim_id": "claim-0",
            "claim_index": 0,
            "condition_consistent": true,
            "discard_code": "off_subject",
            "eligibility_basis": null,
            "entity_consistent": true,
            "event_consistent": true,
            "index_ref": "idx-caf1ed53307b:KH:34",
            "missing_anchor_terms": [
              "albania"
            ],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "reason": "article title is about a different subject than the question",
            "retrieval_score": 0.6353930830955505,
            "source_id": "url:https://www.geonames.org/countries/KH/#bb072723c8d2",
            "title": "Cambodia",
            "title_covers_event": false,
            "topic_coverage": 0.0,
            "url": "https://www.geonames.org/countries/KH/"
          },
          {
            "about_subject": false,
            "article_covers_event": false,
            "article_id": "GR",
            "article_key": "url:https://www.geonames.org/countries/GR/",
            "article_key_scope": "global",
            "chunk_id": 1,
            "claim_id": "claim-0",
            "claim_index": 0,
            "condition_consistent": true,
            "discard_code": "off_subject",
            "eligibility_basis": null,
            "entity_consistent": true,
            "event_consistent": true,
            "index_ref": "idx-caf1ed53307b:GR:1",
            "missing_anchor_terms": [
              "albania"
            ],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "reason": "article title is about a different subject than the question",
            "retrieval_score": 0.5026056170463562,
            "source_id": "url:https://www.geonames.org/countries/GR/#82834eb7e07e",
            "title": "Greece",
            "title_covers_event": false,
            "topic_coverage": 0.0,
            "url": "https://www.geonames.org/countries/GR/"
          },
          {
            "about_subject": false,
            "article_covers_event": false,
            "article_id": "CY",
            "article_key": "url:https://www.geonames.org/countries/CY/",
            "article_key_scope": "global",
            "chunk_id": 0,
            "claim_id": "claim-0",
            "claim_index": 0,
            "condition_consistent": true,
            "discard_code": "off_subject",
            "eligibility_basis": null,
            "entity_consistent": true,
            "event_consistent": true,
            "index_ref": "idx-caf1ed53307b:CY:0",
            "missing_anchor_terms": [
              "albania"
            ],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "reason": "article title is about a different subject than the question",
            "retrieval_score": 0.43168196082115173,
            "source_id": "url:https://www.geonames.org/countries/CY/#06da230423d6",
            "title": "Cyprus",
            "title_covers_event": false,
            "topic_coverage": 0.0,
            "url": "https://www.geonames.org/countries/CY/"
          }
        ],
        "evaluated_evidence": [
          {
            "about_subject": true,
            "article_covers_event": true,
            "article_id": "AL",
            "article_key": "url:https://www.geonames.org/countries/AL/",
            "article_key_scope": "global",
            "chunk_id": 33,
            "claim_id": "claim-0",
            "claim_index": 0,
            "claim_names_in_premise": false,
            "condition_consistent": true,
            "discard_code": "candidate_retained_for_nli",
            "eligibility_basis": "lexical_subject",
            "entity_consistent": true,
            "event_consistent": true,
            "fact_score": 2,
            "index_ref": "idx-caf1ed53307b:AL:33",
            "match_score": 1,
            "missing_anchor_terms": [],
            "missing_event_identifiers": [],
            "missing_numbers": [],
            "nli_label": "contradiction",
            "nli_output_shape": "list[dict]",
            "nli_score": 0.9998899698257446,
            "office_holder_consistent": true,
            "premise_windows": [
              {
                "fact_score": 2,
                "nli_label": "contradiction",
                "premise": "The capital of Albania is Tirana.",
                "probabilities": {
                  "contradiction": 0.9998899698257446,
                  "entailment": 1.9222066839574836e-05,
                  "neutral": 9.086769568966702e-05
                },
                "title_dependent": false,
                "token_count": 18,
                "value_relation": "none"
              }
            ],
            "probabilities": {
              "contradiction": 0.9998899698257446,
              "entailment": 1.9222066839574836e-05,
              "neutral": 9.086769568966702e-05
            },
            "quantity_kinds": [],
            "quantity_scope_aligned": true,
            "relation_aligned": true,
            "relevant_evidence": "The capital of Albania is Tirana.",
            "retrieval_score": 0.8648569583892822,
            "source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
            "title": "Albania",
            "title_covers_event": false,
            "topic_coverage": 1.0,
            "url": "https://www.geonames.org/countries/AL/",
            "value_relation": "none"
          }
        ],
        "evidence_chunk_id": 33,
        "evidence_source_id": "url:https://www.geonames.org/countries/AL/#602e38d656d6",
        "evidence_title": "Albania",
        "ignored_contradictions": [],
        "ignored_support": [],
        "index_version": "idx-caf1ed53307b",
        "latency_breakdown_ms": {
          "nli": 113.1,
          "retrieval": 48.25,
          "total": 163.66
        },
        "latency_ms": 163.66,
        "max_premise_windows": 3,
        "min_nli_score": 0.5,
        "min_retrieval_score": 0.45,
        "min_topic_coverage": 0.5,
        "nli_label": "contradiction",
        "nli_model": "cross-encoder/nli-deberta-v3-small",
        "nli_output_shape": "list[dict]",
        "retrieval_margin": 0.15,
        "retrieval_score": 0.8648569583892822,
        "retrieved_counts": [
          {
            "claim_id": "claim-0",
            "claim_index": 0,
            "retrieved_count": 6
          }
        ],
        "score_meaning": "NLI probability of the label that decided the result (entailment for SUPPORT, contradiction for REJECT) on the deciding evidence chunk; 0 for UNSURE. A class probability from one model, not a calibrated probability that the answer is correct.",
        "supporting": [],
        "thresholds_calibrated": false,
        "top_k": 3,
        "topic_margin": 0.3,
        "unchecked_claims": [],
        "unsure_reason": null
      }
    }
  },
  {
    "verifier_name": "rule",
    "state": "abstention",
    "report": {
      "verifier_name": "rule",
      "score": 0.0,
      "passed": false,
      "reasoning": "No supported deterministic rule matched the question.",
      "metadata": {
        "decision": "UNSURE",
        "latency_ms": 0.03,
        "rule": "unsupported",
        "rule_kind": null,
        "score_meaning": "Deterministic rule outcome bit: 1 when the check passed, 0 when it failed. Not a probability."
      }
    }
  },
  {
    "verifier_name": "semantic",
    "state": "directional",
    "report": {
      "verifier_name": "semantic",
      "score": 0.7771412281518978,
      "passed": true,
      "reasoning": "Semantic similarity score: 0.7771. Support threshold: 0.50; reject threshold: 0.30. Compared text is semantically close to the reference.",
      "metadata": {
        "compared_text": "What is the capital of Albania? The capital of Albania is Phnom Penh.",
        "comparison_method": "question_answer_vs_context",
        "decision": "SUPPORT",
        "latency_ms": 46.31,
        "model": "all-MiniLM-L6-v2",
        "raw_similarity": 0.7771412281518978,
        "reject_threshold": 0.3,
        "score_meaning": "Cosine similarity between the compared text and the reference, clipped to [0, 1]. Measures resemblance of meaning, not factual correctness; not a probability and not calibrated.",
        "support_threshold": 0.5,
        "threshold": 0.5,
        "thresholds_calibrated": false
      }
    }
  }
]
```

Aggregation: reputation_weighted; numerical failed at -0.999889969826; public uncertain; contributors 1; required ['direct_fact']; achieved ['direct_fact']; reasons ['minimum_contributors'].
```json
{
  "aggregation": "log_odds",
  "aggregation_id": "reputation_weighted",
  "aggregation_version": "log_odds_v1",
  "dependency_assumptions": [],
  "dependency_configuration_id": null,
  "dependency_version": null,
  "domain": "general",
  "fallback": null,
  "groups": [],
  "lower_cut": -0.55,
  "missing_reports": [],
  "raw_score": -0.9998899698257446,
  "reputation_snapshot_id": "0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3",
  "score": -0.99989,
  "status": "failed",
  "team": [
    "evidence",
    "rule"
  ],
  "threshold": 0.55,
  "upper_cut": 0.55,
  "validation_id": "factual-capitals42-v1-development-AL-incorrect",
  "votes": [
    {
      "abstained": false,
      "confidence": 0.9998899698257446,
      "contribution": -3.713163461722697,
      "failure_group_id": null,
      "included": true,
      "inclusion_reason": "included",
      "normalized_strength": -0.9998899698257446,
      "passed": false,
      "reliability_strength": 0.9523809523809523,
      "reputation": 0.9761904761904762,
      "validation_id": "factual-capitals42-v1-development-AL-incorrect",
      "verifier_name": "evidence",
      "weight": 3.7135720667043066
    },
    {
      "abstained": true,
      "confidence": 0.0,
      "contribution": 0.0,
      "failure_group_id": null,
      "included": false,
      "inclusion_reason": "abstention",
      "normalized_strength": null,
      "passed": false,
      "reliability_strength": 0.0,
      "reputation": 0.5,
      "validation_id": "factual-capitals42-v1-development-AL-incorrect",
      "verifier_name": "rule",
      "weight": 0.0
    }
  ]
}
```

Aggregation: dependency_group; numerical failed at -0.999889969826; public uncertain; contributors 1; required ['direct_fact']; achieved ['direct_fact']; reasons ['minimum_contributors'].
```json
{
  "aggregation": "dependency_group",
  "aggregation_id": "dependency_group",
  "aggregation_version": "groups_v1",
  "dependency_assumptions": [
    "configured compromise pathways; conservative connected components",
    "unresolved verifiers share one unknown compromise pathway",
    "observed provenance is audit-only and never rewrites this registry"
  ],
  "dependency_configuration_id": "4ca2f113fd7b9ae042812ec16b0d5acc33eb4949018596936e66e652e3b13a1d",
  "dependency_version": "observed-shared-models-and-unresolved-v1",
  "domain": "general",
  "fallback": null,
  "groups": [
    {
      "active_members": [
        "evidence"
      ],
      "contribution": -0.9522761617388044,
      "fallback": null,
      "group_id": "cd406da454f8dbac024fd3ded624db5b0b9cb47a6297882e75553de387c5f374",
      "influence": 0.9523809523809523,
      "reliability_sum": 0.9523809523809523,
      "score": -0.9998899698257446
    }
  ],
  "lower_cut": -0.55,
  "missing_reports": [],
  "raw_score": -0.9998899698257446,
  "reputation_snapshot_id": "0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3",
  "score": -0.99989,
  "status": "failed",
  "team": [
    "evidence",
    "rule"
  ],
  "threshold": 0.55,
  "upper_cut": 0.55,
  "validation_id": "factual-capitals42-v1-development-AL-incorrect",
  "votes": [
    {
      "abstained": false,
      "confidence": 0.9998899698257446,
      "contribution": -0.9522761617388044,
      "failure_group_id": "cd406da454f8dbac024fd3ded624db5b0b9cb47a6297882e75553de387c5f374",
      "included": true,
      "inclusion_reason": "included",
      "normalized_strength": -0.9998899698257446,
      "passed": false,
      "reliability_strength": 0.9523809523809523,
      "reputation": 0.9761904761904762,
      "validation_id": "factual-capitals42-v1-development-AL-incorrect",
      "verifier_name": "evidence",
      "weight": 0.9523809523809523
    },
    {
      "abstained": true,
      "confidence": 0.0,
      "contribution": 0.0,
      "failure_group_id": "cd406da454f8dbac024fd3ded624db5b0b9cb47a6297882e75553de387c5f374",
      "included": false,
      "inclusion_reason": "abstention",
      "normalized_strength": null,
      "passed": false,
      "reliability_strength": 0.0,
      "reputation": 0.5,
      "validation_id": "factual-capitals42-v1-development-AL-incorrect",
      "verifier_name": "rule",
      "weight": 0.0
    }
  ]
}
```

## Validation

{
  "artifact_id": "238adc94fa3d6d81f60740d4cb585c52befa1748ea2ca1ee7aa2e169cf464236",
  "policy_id": "99d6d6369341c48f919c8a8f2a1643f0320821afa15bf9d323e816e5e46dad30",
  "matrix_id": "25303e5c2f8d8db609c812b780e9373923204743ee459d56e0000b0cd94504bc",
  "reputation_snapshot_id": "0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3",
  "calibration_id": "d5fd225b45d0b09fb54de3a07344415604638ce004fa8b51dac6218bd25a2793",
  "certificate_valid": true,
  "provider_reload_valid": true,
  "retained_report_runtime_parity": true,
  "live_real_resources_compatible": true,
  "final_payload_access_guard_active": true,
  "final_collection_or_evaluation": false,
  "attempts": 320,
  "additional_inference_attempts": 0,
  "application_source_unchanged": true,
  "original_fit_driver_preserved": true,
  "arithmetic_original_files_unchanged": 10,
  "reproducibility": {
    "equivalent": true,
    "matrix_atol": 1e-12,
    "probability_atol": 1e-12,
    "relative_tolerance": 0.0,
    "reputation_atol": 1e-12
  },
  "configuration_digest": "91cbe3ee65ba3f46d7c7fe85a676c24e16a108a6a87084099a001943decd63b7",
  "report_driver_sha256": "c1f82a7b0d464a96db21d2a111735c7048082ca90ffbf4703870e2b0c377463e"
}

All fourteen per-strategy/per-attack metrics and full representative traces are in development-report.json.
Equivalent payoff rows do not establish aggregation superiority. No study settings were tuned after development.
Initial fit/report phases encountered a sandbox metadata denial and a report-only dataclass serialization defect; report phase alone was corrected and rerun. Artifact, calibration and recordings were preserved.
