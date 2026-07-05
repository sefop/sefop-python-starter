# SEFOP - Python Starter

**Reference implementation of [SEFOP](https://github.com/sefop) for Python in a simplified manner**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)
[![CI — Unit Tests](https://github.com/sefop/sefop-python/actions/workflows/ci-unit-tests.yml/badge.svg)](https://github.com/sefop/sefop-python/actions/workflows/ci-unit-tests.yml)
[![CI — Integration Tests](https://github.com/sefop/sefop-python/actions/workflows/ci-integration-tests.yml/badge.svg)](https://github.com/sefop/sefop-python/actions/workflows/ci-integration-tests.yml)

---

## Problem description

This repo solves a knapsack problem. Given a **budget** and a **weight limit**, pick the combination of products that **maximizes total calories**.

### Mathematical formulation

**Sets**
- $I$: set of candidate products, indexed by $i \in I$

**Parameters**
- $\text{price}_i$, $\text{weight}_i$, $\text{calories}_i$: unit price (USD), unit weight (kg), and nutritional value of product $i \in I$
- $B$: budget, in USD (`max_budget_usd`)
- $W$: weight limit, in kg (`max_weight_kg`)

**Decision variable**
- $x_i \in \mathbb{Z}_{\ge 0}$ for each $i \in I$: number of units of product $i$ selected

**Objective** — maximize total calories:

$$\max \sum_{i \in I} \text{calories}_i \cdot x_i$$

**Constraints**

$$\sum_{i \in I} \text{price}_i \cdot x_i \le B \qquad \text{(budget)}$$

$$\sum_{i \in I} \text{weight}_i \cdot x_i \le W \qquad \text{(weight limit)}$$

$$x_i \in \mathbb{Z}_{\ge 0} \quad \forall i \in I \qquad \text{(non-negativity \& integrality)}$$

Because $x_i$ has no upper bound, this is an **unbounded knapsack problem**: any number of units of a product may be chosen, which is why integrality must be enforced explicitly rather than relying on a 0/1 selection variable.

### Example — Data from [`data/2/data.json`](data/2/data.json)

| Product   | Price  | Weight  | Calories |
|-----------|--------|---------|----------|
| Apple     | $1.00  | 0.50 kg | 100      |
| Chocolate | $5.00  | 1.00 kg | 50       |

**Constraints:** budget $10.00 and weight limit 2.00 kg

**Optimal solution:**

| Product   | Units | Cost   | Weight  | Calories |
|-----------|-------|--------|---------|----------|
| Apple     | 4     | $4.00  | 2.00 kg | 400      |
| Chocolate | 0     | $0.00  | 0.00 kg | 0        |

| Total calories | Total cost / Budget | Total weight / Max weight |
|-----------------|----------------------|----------------------------|
| 400             | $4.00 / $10.00       | 2.00 kg / 2.00 kg          |

The solver picks 4 apples — chocolate costs 10× more per calorie, so it never appears in the optimal solution.

---

## Repository structure

```
src/
  domain/               # pure entities — Product, Request, Recommendation
  services/             # data loading and application service
  engine/
    orchestrator.py     # pipeline coordinator: pre → strategy → post
    preprocessing/      # filter infeasible products before solving
    optimization/       # MIP solver and greedy heuristic
    postprocessing/     # sort and refine the recommendation
  cli.py                # CLI entry point
tests/                  # mirrors src/ structure
data/                   # sample problem instances
```

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/sefop/sefop-python-starter.git
cd sefop-python-starter
```

### 2. Create a virtual environment using Python 3.12
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

**What breaks if you skip this step?** `pytest` still works, since `pyproject.toml` adds `src` to the path just for pytest. But `python -m cli 1` will fail with an import error — `cli.py` imports `domain`, `engine`, etc. as top-level packages, and without the editable install Python has no way to find them under `src/` outside of pytest.

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
pytest tests/engine/          # engine, strategies, pre/postprocessing tests
```

---

## Code quality

CI runs two checks before the test suite; both are fast, so run them locally before pushing to avoid a red PR.

### Format check (black)
```bash
black --check src tests   # verify formatting only, no changes written
black src tests           # reformat in place
```
Configuration (line length, target Python version) lives in `pyproject.toml`'s `[tool.black]` section, so the local command and CI always agree.

### Type check (mypy)
```bash
mypy
```
Configuration lives in `pyproject.toml`'s `[tool.mypy]` section.

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
2. **`services/`** — Data loading (`JsonDataLoader`) and the application service that wires loading to the engine
3. **`engine/orchestrator.py`** — Pipeline coordinator: runs preprocessing → picks a strategy → runs postprocessing
4. **`engine/preprocessing/`** — Filters out products that can never be selected (individually infeasible)
5. **`engine/optimization/`** — Solver implementations:
   - **Greedy heuristic** — fast, approximate solution for large problems
   - **MIP solver** — exact optimal solution via HiGHS for small problems
6. **`engine/postprocessing/`** — Refines the recommendation (e.g., sorts products by quantity)
7. **`cli.py`** — Entry point that loads data and calls the solver

---
