# Isolated engineering validation environment

No production requirements file, installed production environment, model or service is changed. This environment exists only for schema/planning/filesystem/synthetic-boundary tests and is not a research calibration or live resource certificate.

Reproduced original failure with the original isolated test interpreter: eager verifier-package imports reach Sentence Transformers 6.3.0 /Transformers 5.22.2, whose installed runtime check requires torch>=2.6, while the Intel Mac environment contains torch2.2.2 and NumPy2.5.4. The recorded traceback ends NameError nn; a NumPy ABI warning also appears. See validation/import-failure-reproduced.log. Missing httpx in the system interpreter is separate; it is already declared in requirements.txt and installed in the test venv.

Replacement environment: a separate isolated virtual environment selected through `TEST_VENV`, Python3.12 Intel macOS. Installed unchanged requirements-verifier-collection.txt with **test-only constraints** in validation/test-constraints.txt. Torch2.2.2 retains the available Intel Mac wheel. Sentence Transformers3.4.1 declares torch>=1.11 and transformers>=4.41,<5; Transformers4.48.3 provides that compatible generation; NumPy1.26.4 matches the installed torch wheel's NumPy1.x ABI. This is an explicit compatible older test line, not an arbitrary sequence of production downgrades and not a model-loading recommendation.

Primary version metadata consulted: [Sentence Transformers3.4.1](https://pypi.org/pypi/sentence-transformers/3.4.1/json), [Transformers4.48.3](https://pypi.org/pypi/transformers/4.48.3/json). The full install/import logs remain local-only; validation/public-results.json summarizes fresh results and test-environment.freeze.txt records the public package resolution; actual execution, not these constraints alone, determines test outcomes. No production lock is replaced.

Reproduction (new empty environment path):

```sh
export TEST_VENV="$(mktemp -d)"
python3 -m venv "$TEST_VENV"
export TEST_PYTHON="$TEST_VENV/bin/python"
export HF_HOME="$(mktemp -d)"
"$TEST_PYTHON" -m pip install -r requirements-verifier-collection.txt -c docs/research_v1-recording-handoff/validation/test-constraints.txt
"$TEST_PYTHON" -m pip install --only-binary=:all: "psycopg2-binary==2.9.13"
"$TEST_PYTHON" -m pip check
```

Installation downloads packages only; tests disable network and model/provider access. Use writable temporary HF_HOME/HUGGINGFACE_HUB_CACHE/TRANSFORMERS_CACHE directories if needed; no model cache is populated. Exact tested resolution is in validation/test-environment.freeze.txt and the installation report. Future hosts must reproduce or revalidate compatibility, not treat this as a historical runtime binding. See final-review.md for actual pass/fail/assertion counts.

`TEST_PYTHON` must name the compatible isolated interpreter. Export `RESEARCH_V1_ARTIFACT_DIR` to the separately authorized ZIP directory for private-evidence checks; no machine-specific value is stored here. Run commands from the repository root. `HF_HOME` points to an empty writable directory created for this test run. Preserve its location locally if reproducing a failure; never commit cache contents or local installation logs.

## Database-driver import dependency for policy regressions

The existing source imports `psycopg2` through `database.py`, reached by benchmark/package initialization during seven policy-source compatibility cases. Neither production requirements file declares a Psycopg distribution. The previous failure was an environment import gap, not a failed policy assertion. The isolated test environment now includes **psycopg2-binary 2.9.13**, which supplies the required `psycopg2` module; no production dependency manifest or database code is changed. This test-only wheel choice follows the [official Psycopg installation documentation](https://www.psycopg.org/docs/install.html#quick-install), not a production deployment recommendation.

Run the 11 read-only policy regressions with `"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py regression`. The runner disables dotenv loading and blocks database connection entry points, sockets, live verifier/model calls and policy fitting. No database service or migration is needed for these tests.
