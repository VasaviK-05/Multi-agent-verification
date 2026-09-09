# Architecture

This document describes the four-layer architecture of the Multi-Agent Answer Validation System and how source folders map to each layer.

## System Flow

```
User Interface
  → Backend API
  → Validation Orchestrator
  → Question Analyzer
  → Verifier Selector
  → Selected Verifier Services
  → Decision Engine
  → Validation Orchestrator
  → Backend API
  → User Interface
```

---

## Layer 1 — Interface & Orchestration

Handles HTTP requests, coordinates the validation pipeline, and returns responses to the client.

| Folder | Responsibility |
|--------|---------------|
| `app/api/` | FastAPI route definitions (`/health`, `/validate`) |
| `app/main.py` | FastAPI application entry point |
| `app/orchestration/` | `ValidationOrchestrator` — coordinates the full pipeline |
| `app/services/` | Application-level service layer (`ValidationService`) |
| `app/utils/` | Configuration and shared utilities |

**Where to add future work:**
- New API endpoints → `app/api/routes.py`
- Pipeline coordination changes → `app/orchestration/validation_orchestrator.py`

---

## Layer 2 — Intelligence & Verification

Analyzes questions, selects verifiers, and runs verification logic.

| Folder | Responsibility |
|--------|---------------|
| `app/analysis/` | `QuestionAnalyzer` — domain and difficulty classification |
| `app/selection/` | `VerifierSelector` — adaptive verifier selection |
| `app/verifiers/` | Individual verifier implementations |
| `app/models/` | Shared Pydantic schemas (`ValidationRequest`, `VerificationResult`, etc.) |

**Verifier services:**
1. `semantic_verifier.py` — Semantic similarity checks
2. `evidence_verifier.py` — Evidence retrieval and verification
3. `rule_verifier.py` — Rule-based validation
4. `confidence_verifier.py` — Confidence estimation

**Where to add future work:**
- Domain/difficulty analysis → `app/analysis/question_analyzer.py`
- Adaptive selection logic → `app/selection/verifier_selector.py`
- New verifier implementations → `app/verifiers/`
- Shared data contracts → `app/models/schemas.py`

---

## Layer 3 — Decision & Learning

Aggregates verifier outputs, manages reputation, and handles feedback.

| Folder | Responsibility |
|--------|---------------|
| `app/decision/` | `DecisionEngine` — aggregates verifier results into a final decision |
| `app/reputation/` | `ReputationManager` — domain-specific verifier reputation (EWMA) |
| `app/feedback/` | `EvaluationService` — feedback, ground truth, learning triggers |

**Where to add future work:**
- Game-theoretic aggregation → `app/decision/decision_engine.py`
- EWMA reputation updates → `app/reputation/reputation_manager.py`
- Feedback and learning loops → `app/feedback/evaluation_service.py`

---

## Layer 4 — PostgreSQL Data Layer

Persistence for validation records, verifier outputs, reputation, and feedback.

| Folder | Responsibility |
|--------|---------------|
| `app/database/models.py` | Data models for stored entities |
| `app/database/repository.py` | Repository pattern for database operations |

**Future stored entities:**
- Validation Records
- Verifier Outputs
- Domain Reputation
- Feedback / Ground Truth

**Where to add future work:**
- ORM models → `app/database/models.py`
- Database queries → `app/database/repository.py`

> The scaffold runs without PostgreSQL. Database integration will be added in a future feature branch.
