# Game-Theoretic Multi-Agent Framework for AI Answer Validation

**A research-oriented AI verification system that decides _which checks to run_, _how much to trust them_, and _when the evidence is insufficient to make a decision_.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Audit%20Storage-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/) [![Tests](https://img.shields.io/badge/Tests-pytest-informational)](tests/) [![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)](docs/)

> **The problem:** LLM-generated answers can sound convincing while being wrong. A single confidence score or a simple majority vote can also be misleading when validators abstain, share dependencies, or rely on unreliable evidence.
>
> **Our approach:** Combine specialized verification, domain-aware reliability, coverage guards, and a **budget-aware, dependency-aware minimax game** for selecting verifier teams and aggregation strategies. The system can explicitly return **uncertain** rather than presenting an unsupported verdict as fact.

## At a glance

| Capability | Implementation |
| --- | --- |
| Four complementary validators | Evidence retrieval, semantic/reference similarity, deterministic rules, model-based confidence |
| Adaptive verification | Question analysis, eligibility and prerequisite checks, coverage-aware verifier selection |
| Reputation and decisions | Domain-specific Beta reputation, reputation-weighted aggregation, dependency-group aggregation |
| Game-theoretic selection | Defender strategies = verifier subset + aggregation; adversarial shared-failure scenarios; minimax mixed strategy solved with SciPy linear programming |
| Reproducible research | Offline recordings, measured verifier costs, empirical payoff matrices, frozen/versioned policy artifacts, held-out evaluation workflows |
| Application engineering | FastAPI, Pydantic, PostgreSQL-backed validation/audit records, execution traces, feedback integration |

## How it works

```text
Question + candidate answer (or generate an answer)
                     |
                     v
           Question / requirement analyzer
                     |
                     v
          Eligibility + capability registry
                     |
          +----------+-----------+
          |                      |
          v                      v
   Baseline selection       Game-mode selection
   (coverage-aware)         (compatible fitted policy)
          |                      |
          +----------+-----------+
                     |
                     v
       Selected verifier(s) execute
        /        |        |       \
   Evidence   Semantic   Rule   Confidence
        \        |        |       /
                     v
     Reputation-weighted OR dependency-aware
                 aggregation
                     |
                     v
     Coverage / contributor / failure guards
                     |
                     v
           PASSED / FAILED / UNCERTAIN
                     |
                     v
        Audit, ground truth, feedback,
         and future reputation updates
```

**Important distinction:** the system does **not** know ground truth at inference time. It estimates support for the submitted answer. Independently sourced ground truth or appropriate external feedback may later update verifier reputation; the system's own decision is not ground truth.

### The four verifier agents

| Verifier | Question it addresses | Key limitation |
| --- | --- | --- |
| **Evidence** | Does retrieved material support the answer? | Retrieval/index quality and relevance affect coverage |
| **Semantic** | Does the answer agree with a supplied reference? | Without an appropriate reference, semantic verification may be uninformative |
| **Rule** | Can deterministic arithmetic or logical constraints validate it? | Applies only to supported rule types |
| **Confidence** | Does model-based assessment support the answer? | Model inference is comparatively expensive and confidence is not proof |

Abstentions are first-class results, **not** automatic negative votes. A high numerical score can still produce a public **uncertain** decision if required coverage or informative-contributor constraints are not met.

## What makes the game engine different?

The game explicitly models **a defender** (the verification system) and **an experimental attacker** (a controlled shared-dependency failure or report manipulation). Verifiers themselves are not assumed to be rational adversarial players.

1. **Enumerate feasible strategies:** eligible verifier subsets paired with either reputation-weighted or dependency-group aggregation, subject to capability, minimum-contributor and budget constraints.
2. **Model correlated failures:** a dependency registry groups checks that may share vulnerable resources, such as an index, reference, or model service.
3. **Build empirical payoffs:** replay recorded verifier reports under clean and controlled attack transformations (forced support/rejection, inflation, suppression), incorporating incorrect-decision penalties, uncertainty, and cost.
4. **Solve the zero-sum game:** use `scipy.optimize.linprog` to minimize worst-case empirical loss across attacker actions.
5. **Deploy only compatible policies:** bind fitted strategies to task, resources, reputation snapshot, execution contract and provenance. Incompatible artifacts must not silently run.

A policy may legitimately choose **one strategy with probability 1**; randomization is not forced for appearance. Feasible team sizes can range from one to four depending on the configured task and requirements. In game mode, the selected team is executed according to the frozen execution contract rather than silently adding unmodeled fallback checks.

**Research caveat:** minimax optimality is relative to the measured payoff matrix, modeled attacks and eligible strategies. It is not a general guarantee of hallucination elimination or robustness to unseen attacks.

Read more: [Game engine](docs/game_engine_foundation.md) · [Offline evaluation](docs/game_offline_evaluation.md) · [Runtime integration](docs/game_runtime_integration.md) · [Dependency aggregation](docs/dependency_aggregation.md).

## Evidence from experiments

This repository includes reproducible engineering studies, not just architecture diagrams.

| Recorded study | What was observed |
| --- | --- |
| Three-task development campaign | **960 verifier attempts** across arithmetic, factual and semantic-equivalence cohorts; the initial 90% clean-coverage requirement was infeasible for all three under the tested constraints |
| Flexible-minimum held-out evaluation | Arithmetic **100%** decision coverage and factual **97.5%** in an 80-example evaluation, using task-conditioned singleton policies; these results do **not** establish an advantage over every baseline |
| Compound-reference verification | Frozen Evidence + Rule policy, with an amended **85%** clean-coverage target; **5/48 uncertain**, **0 incorrect** recorded clean decisions, giving clean loss **0.0208333** at uncertainty penalty 0.2 |
| Live HTTP game-mode audit | A recorded arithmetic validation returned **uncertain** despite a positive numerical score because only one of two required informative contributors was available |

**Interpretation matters:** development findings are not interchangeable with held-out findings; amended thresholds are disclosed; coverage is not accuracy; and a fitted policy is not automatically a deployed policy. The experiments also reveal when abstention, missing references and verifier costs limit practical utility.

Study details: [Multitask results](docs/multitask_policy_results.md) · [Compound verification](docs/compound_reference_fitting_verification_20261105.md) · [Live audit](docs/game_mode_http_audit_20261104.md) · [Research protocol](docs/game_research_protocol.md).

## Architecture and repository guide

```text
app/
  api/              FastAPI routes
  services/         Validation service
  orchestration/    Execution coordination and audit context
  analysis/         Domain, difficulty and requirement analysis
  selection/        Candidate eligibility and baseline selection
  verifiers/        Evidence, semantic, rule and confidence modules
  decision/         Aggregation, normalization, coverage, early termination
  reputation/       Domain-aware reliability and feedback updates
  game/             Strategy enumeration, minimax solver, policy/runtime contracts
    offline/        Recording, attack replay, payoff construction and evaluation
  database/         Persistence repositories and audit records
  feedback/         Ground-truth / feedback handling
docs/               Design, research protocol, studies and verification reports
tests/              Automated regression and component tests
artifacts/          Versioned research/policy artifacts
```

The baseline selector and game engine are **distinct modes**, with shared verification components. Baseline early stopping and fallback behavior must not be mistaken for the fixed-team game evaluation contract.

## Run locally

**Requirements:** Python 3.10+, pip. Some verifier paths additionally require configured models, retrieval assets, a running Ollama service and/or PostgreSQL. Check the relevant setup documents before expecting every verifier or game policy to be available.

```bash
git clone https://github.com/VasaviK-05/Multi-agent-verification.git
cd Multi-agent-verification
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows, activate with `.venv\Scripts\activate`. Configure the environment for your local database/model services; do not commit credentials.

Open **http://127.0.0.1:8000/docs** for the interactive API.

```bash
curl -X POST http://127.0.0.1:8000/validate \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is 510 + 822?","answer":"1332"}'
```

Other application routes include answer generation and generate-and-validate. **A successful HTTP response does not imply that game mode is active**: it requires a configured, compatible policy and resources. See [runtime integration](docs/game_runtime_integration.md) and [policy/resource reconciliation](docs/policy_resource_reconciliation_handoff.md).

### Tests

```bash
pytest
# or inspect individual suites
pytest -v tests/
```

Some integration tests depend on external resources or a database. See the study documents for the exact commands and frozen evaluation environments used for reported results.

## Current status and limitations

This is an **active research prototype**, not a claim of production readiness.

- Policy compatibility and provenance checks intentionally reject stale or mismatched model/index resources; policy fitting, artifact verification and deployment are separate stages.
- Semantic verification requires an appropriate reference; retrieval and model availability affect the actual informative coverage.
- Experiments have **not** demonstrated universal game-theoretic superiority over simpler baselines. Results must be compared at matched coverage, loss and resource budgets.
- Recorded API audit persistence is not equivalent to guaranteed **crash-safe per-attempt checkpoint/resume**; recovery behavior must be validated independently.
- Robustness results concern specified report transformations and experiments, not an unrestricted adversary.

## Team and contributions

Built collaboratively by a four-person capstone team. Contributions span **AI systems and decision engineering, verifier implementation, API/integration, database/audit persistence, and evaluation**. See [GitHub's commit history](../../commits/main) and [contributors](../../graphs/contributors) for attributable code contributions.

Team members can pin this public repository to their profiles; GitHub contribution graphs depend on qualifying commits and linked author email addresses. Individual responsibilities should be credited using verified GitHub handles rather than guessed identities.

## Documentation

[Architecture](docs/architecture.md) · [Decision formulas](docs/decision_formulas.md) · [Policy build](docs/game_policy_build.md) · [Verifier cost calibration](docs/verifier_cost_calibration.md) · [Publication notes](docs/PUBLICATION.md)

---

**Project focus:** trustworthy AI evaluation · multi-agent systems · game theory · robust optimization · RAG · backend engineering · empirical software research.
