Command:

`python -m pytest tests/test_experiment3_ablation_v1.py tests/test_experiment3_visualizations.py tests/test_dependency_aggregation.py tests/test_experiment3_synthetic.py tests/test_experiment3_empirical_integration.py evaluation/tests/test_experiment3_dependency_heatmap.py --tb=line -q --continue-on-collection-errors`

Result: 102 passed, 1 error. Pytest exit code 1.

The error is collection of `tests/test_experiment3_synthetic.py`:

`ImportError: cannot import name 'CONTROLLED_SYNTHETIC_ASSUMPTION' from 'app.game.dependencies'`.

`app/game/dependencies.py` was not modified for ablation v1. The other five files collected and passed. That includes `tests/test_experiment3_ablation_v1.py`, which checks the registries, failure scope, unchanged reports, matched inputs, group bootstrap, missing cells, and the completed result file.
