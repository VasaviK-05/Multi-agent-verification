# All-strategy diagnosis (before changes)

Development only; every strategy and attack retained.

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
    "log_odds": 0.0
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
    "log_odds": 3.7135720667043066
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
    "log_odds": 0.0
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
    "log_odds": 3.7135720667043066
  }
]

## ['confidence', 'evidence'] / reputation_weighted

Cost 12903.808043734 ms; worst objective 0.604600591.
- clean: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000; false accept/reject 20.0/0.0; validation loss 0.505000000; objective 0.604600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000; false accept/reject 0.0/19.0; validation loss 0.480000000; objective 0.579600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.299600591; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence'] / dependency_group

Cost 12903.808043734 ms; worst objective 0.604600591.
- clean: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000; false accept/reject 20.0/0.0; validation loss 0.505000000; objective 0.604600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000; false accept/reject 0.0/19.0; validation loss 0.480000000; objective 0.579600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109600591; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.299600591; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['evidence', 'rule'] / reputation_weighted

Cost 181.689941246 ms; worst objective 0.201402410.
- clean: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['evidence', 'rule'] / dependency_group

Cost 181.689941246 ms; worst objective 0.201402410.
- clean: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201402410; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['evidence', 'semantic'] / reputation_weighted

Cost 233.181544984 ms; worst objective 0.201799858.
- clean: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201799858; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201799858; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201799858; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201799858; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201799858; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['evidence', 'semantic'] / dependency_group

Cost 233.181544984 ms; worst objective 0.501799858.
- clean: coverage 1.000000; false accept/reject 0.0/0.0; validation loss 0.000000000; objective 0.001799858; contributors {2: 40}; reasons {}.
- forced_support: coverage 1.000000; false accept/reject 20.0/0.0; validation loss 0.500000000; objective 0.501799858; contributors {2: 40}; reasons {}.
- forced_rejection: coverage 1.000000; false accept/reject 0.0/20.0; validation loss 0.500000000; objective 0.501799858; contributors {2: 40}; reasons {}.
- confidence_inflation: coverage 1.000000; false accept/reject 0.0/0.0; validation loss 0.000000000; objective 0.001799858; contributors {2: 40}; reasons {}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201799858; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence', 'rule'] / reputation_weighted

Cost 12903.935088732 ms; worst objective 0.604601571.
- clean: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000; false accept/reject 20.0/0.0; validation loss 0.505000000; objective 0.604601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000; false accept/reject 0.0/19.0; validation loss 0.480000000; objective 0.579601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.299601571; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence', 'rule'] / dependency_group

Cost 12903.935088732 ms; worst objective 0.604601571.
- clean: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000; false accept/reject 20.0/0.0; validation loss 0.505000000; objective 0.604601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000; false accept/reject 0.0/19.0; validation loss 0.480000000; objective 0.579601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109601571; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.299601571; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence', 'semantic'] / reputation_weighted

Cost 12955.426692471 ms; worst objective 0.604999019.
- clean: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109999019; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000; false accept/reject 20.0/0.0; validation loss 0.505000000; objective 0.604999019; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000; false accept/reject 0.0/19.0; validation loss 0.480000000; objective 0.579999019; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.109999019; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.299999019; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence', 'semantic'] / dependency_group

Cost 12955.426692471 ms; worst objective 0.599999019.
- clean: coverage 0.975000; false accept/reject 0.0/0.0; validation loss 0.005000000; objective 0.104999019; contributors {3: 39, 2: 1}; reasons {}.
- forced_support: coverage 1.000000; false accept/reject 20.0/0.0; validation loss 0.500000000; objective 0.599999019; contributors {3: 39, 2: 1}; reasons {}.
- forced_rejection: coverage 1.000000; false accept/reject 0.0/20.0; validation loss 0.500000000; objective 0.599999019; contributors {3: 39, 2: 1}; reasons {}.
- confidence_inflation: coverage 0.975000; false accept/reject 0.0/0.0; validation loss 0.005000000; objective 0.104999019; contributors {3: 39, 2: 1}; reasons {}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.299999019; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['evidence', 'rule', 'semantic'] / reputation_weighted

Cost 233.308589982 ms; worst objective 0.201800838.
- clean: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201800838; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201800838; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201800838; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201800838; contributors {1: 40}; reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201800838; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['evidence', 'rule', 'semantic'] / dependency_group

Cost 233.308589982 ms; worst objective 0.501800838.
- clean: coverage 1.000000; false accept/reject 0.0/0.0; validation loss 0.000000000; objective 0.001800838; contributors {2: 40}; reasons {}.
- forced_support: coverage 1.000000; false accept/reject 20.0/0.0; validation loss 0.500000000; objective 0.501800838; contributors {2: 40}; reasons {}.
- forced_rejection: coverage 1.000000; false accept/reject 0.0/20.0; validation loss 0.500000000; objective 0.501800838; contributors {2: 40}; reasons {}.
- confidence_inflation: coverage 1.000000; false accept/reject 0.0/0.0; validation loss 0.000000000; objective 0.001800838; contributors {2: 40}; reasons {}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.201800838; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted

Cost 12955.553737469 ms; worst objective 0.605000000.
- clean: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.110000000; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000; false accept/reject 20.0/0.0; validation loss 0.505000000; objective 0.605000000; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000; false accept/reject 0.0/19.0; validation loss 0.480000000; objective 0.580000000; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000; false accept/reject 0.0/0.0; validation loss 0.010000000; objective 0.110000000; contributors {2: 39, 1: 1}; reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.300000000; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group

Cost 12955.553737469 ms; worst objective 0.600000000.
- clean: coverage 0.975000; false accept/reject 0.0/0.0; validation loss 0.005000000; objective 0.105000000; contributors {3: 39, 2: 1}; reasons {}.
- forced_support: coverage 1.000000; false accept/reject 20.0/0.0; validation loss 0.500000000; objective 0.600000000; contributors {3: 39, 2: 1}; reasons {}.
- forced_rejection: coverage 1.000000; false accept/reject 0.0/20.0; validation loss 0.500000000; objective 0.600000000; contributors {3: 39, 2: 1}; reasons {}.
- confidence_inflation: coverage 0.975000; false accept/reject 0.0/0.0; validation loss 0.005000000; objective 0.105000000; contributors {3: 39, 2: 1}; reasons {}.
- suppression: coverage 0.000000; false accept/reject 0.0/0.0; validation loss 0.200000000; objective 0.300000000; contributors {0: 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
