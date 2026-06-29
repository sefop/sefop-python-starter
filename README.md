# SEFOP - Python Starter

**Reference implementation of [SEFOP](https://github.com/sefop) for Python**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)
[![CI — Unit Tests](https://github.com/sefop/sefop-python/actions/workflows/ci-unit-tests.yml/badge.svg)](https://github.com/sefop/sefop-python/actions/workflows/ci-unit-tests.yml)
[![CI — Integration Tests](https://github.com/sefop/sefop-python/actions/workflows/ci-integration-tests.yml/badge.svg)](https://github.com/sefop/sefop-python/actions/workflows/ci-integration-tests.yml)

---

## What problem does this solve?

Given a **budget** and a **weight limit**, pick the combination of products that **maximizes total calories**.

This is known as the Knapsack problem — a classic in operations research.

### Example — [`data/2/data.json`](data/2/data.json)

| Product   | Price  | Weight  | Calories |
|-----------|--------|---------|----------|
| Apple     | $1.00  | 0.50 kg | 100      |
| Chocolate | $5.00  | 1.00 kg | 50       |

**Constraints:** budget $10.00 · weight limit 2.00 kg

**Optimal solution:**
```
Products selected:
  apple        x4  (400 cal, $4.00, 2.00 kg)
Total calories : 400
Total cost     : $4.00
Total weight   : 2.00 kg
```

The solver picks 4 apples — chocolate costs 10× more per calorie, so it never appears in the optimal solution.

---

## Repository structure

```
src/
  domain/               # pure entities — no imports from other folders
  services/             # orchestration + data loading
  optimization/         # solving logic
  dependencies.py       # composition root
  cli.py                # CLI entry point
tests/                  # automatic tests
data/                   # sample instances
docs/                   # guides and documentation
```

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/sefop/sefop-python-starter.git
cd sefop-python-starter
```

### 2. Create a virtual environment
```bash
py -3.12 -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux
```

### 3. Install dependencies and the package
```bash
pip install -r requirements.txt
pip install -e .
```

The `-e` flag installs the package in **editable mode**, making your source code directly importable. This is the standard Python development practice — no need to set `PYTHONPATH` or reinstall when you edit code.

---

## Testing

### Run all tests
```bash
pytest
```

### Run unit tests only
```bash
pytest -m "not integration"
```

### Run integration tests only
```bash
pytest -m integration
```


### Run tests by layer
```bash
pytest tests/domain/          # domain unit tests only
pytest tests/services/        # service tests only
pytest tests/optimization/    # optimization + MIP tests
```

---

## Usage

### Solve a knapsack optimization request from the CLI (command line interface)
```bash
python -m cli 1  # solve request from data/1/data.json
python -m cli 2  # solve request from data/2/data.json
```

---

## How it works

This project demonstrates **Clean Architecture** applied to optimization:

1. **`domain/`** — Pure business logic (Product, Request, Recommendation) with no external dependencies
2. **`services/`** — Orchestration and data loading (Engine selects a solver strategy)
3. **`optimization/`** — Solver implementations:
   - **Greedy heuristic** — fast, approximate solution for large problems
   - **MIP solver** — exact optimal solution via HiGHS for small problems
4. **`cli.py`** — Entry point that loads data and calls the solver
5. **`dependencies.py`** — Composition root that wires all layers together

The Engine automatically chooses the right solver based on problem size (≤50 products → MIP; larger → greedy).

---

## Development workflow

After `pip install -e .`, your code is live:
- Edit any file in `src/` → changes are instant (no reinstall)
- Run tests anytime: `python pytest`
- Run CLI anytime: `python -m cli 1`

---

