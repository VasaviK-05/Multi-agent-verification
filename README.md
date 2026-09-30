# Multi-Agent Answer Validation System

A final-year research project that validates answers using multiple independent verifier agents, aggregates their outputs, and produces a final validation decision.

## Project Objective

Build a multi-agent system that evaluates whether a given answer correctly addresses a question. Multiple specialized verifiers (semantic, evidence, rule-based, confidence) independently assess the answer. A decision engine aggregates their results into a final validation outcome.

This repository currently contains the shared system scaffold. Individual verification and decision algorithms will be implemented incrementally in separate feature branches.

## High-Level Architecture

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

See [docs/architecture.md](docs/architecture.md) for the four-layer architecture and folder mapping.

The difficulty score, verifier-count rule, Beta reputation, decision score, and early-stop rule are written out in [docs/decision_formulas.md](docs/decision_formulas.md). That note separates published formulas, local design choices, and constants that are not calibrated yet.

## Repository Structure

```
app/
├── main.py                  # FastAPI application entry point
├── api/                     # HTTP route definitions
├── models/                  # Shared Pydantic schemas
├── orchestration/           # Validation pipeline orchestrator
├── analysis/                # Question domain/difficulty analysis
├── selection/               # Adaptive verifier selection
├── verifiers/               # Individual verifier implementations
├── decision/                # Weighted decision score and early stopping
├── reputation/              # Domain-specific Beta reputation
├── benchmark/               # Offline comparison runner (no stored results)
├── feedback/                # Feedback and evaluation service
├── services/                # Application-level service layer
├── database/                # PostgreSQL models and repository (placeholder)
└── utils/                   # Configuration and utilities

tests/                       # pytest test suite
docs/                        # Architecture documentation
```

### Folder Responsibilities

| Folder | Layer | Purpose |
|--------|-------|---------|
| `app/api/` | Interface | FastAPI routes (`/health`, `/validate`) |
| `app/orchestration/` | Interface | Coordinates the validation pipeline |
| `app/services/` | Interface | Application service layer |
| `app/analysis/` | Intelligence | Question domain and difficulty analysis |
| `app/selection/` | Intelligence | Verifier selection logic |
| `app/verifiers/` | Intelligence | Semantic, evidence, rule, confidence verifiers |
| `app/models/` | Shared | Pydantic request/response schemas |
| `app/decision/` | Decision | Aggregates verifier results |
| `app/reputation/` | Decision | Verifier reputation management |
| `app/feedback/` | Decision | Feedback and ground truth handling |
| `app/database/` | Data | PostgreSQL persistence (placeholder) |
| `app/utils/` | Shared | Configuration |

## Local Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd multi-agent-verification

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template (optional)
cp .env.example .env
```

## Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

- Health check: `GET http://localhost:8000/health`
- Validate: `POST http://localhost:8000/validate`

Example validation request:

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?", "answer": "Paris"}'
```

Interactive API docs: `http://localhost:8000/docs`

## Running Tests

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```
