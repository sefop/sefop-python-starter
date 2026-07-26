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

$$x_i \in \mathbb{Z}_{\ge 0} \quad \forall i \in I \qquad \text{(non-negativity and integrality)}$$

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

This project follows a simplified **Clean Architecture**: three layers
(`domain/`, `use_cases/`, `adapters/`), full manual dependency injection, and
a single composition root (`bootstrap.py`) that wires everything together.

```
src/
├── cli.py                     # argparse subparsers + dispatch only — no wiring
├── bootstrap.py                # composition root — the only place concrete
│                                # adapters and use cases get constructed
├── settings.py                 # plain dataclass: folder_path, solver_name, output_folder_path
├── domain/                     # pure entities — Product, Request, Recommendation
├── use_cases/
│   ├── ports/                          # abstract interfaces (ABCs) the use cases depend on
│   │   ├── base_data_loader.py
│   │   ├── base_result_writer.py       # also defines TIMESTAMP_FORMAT
│   │   ├── base_request_discovery.py
│   │   └── base_solution_loader.py
│   ├── optimization_response.py        # result of the two "solve" use cases
│   ├── evaluation_response.py          # result of the "evaluate" use case
│   ├── use_case_solve_single_request.py         # solve one request
│   ├── use_case_solve_multiple_requests.py      # solve every request in a folder
│   ├── use_case_evaluate_solution_for_request.py # feasibility-check a candidate solution
│   └── solving/                        # internal implementation detail of the
│       │                                # solve use cases — not a top-level layer
│       ├── orchestrator.py             # pipeline coordinator: pre → strategy → post
│       ├── preprocessing/              # filter infeasible products before solving
│       ├── postprocessing/             # sort and refine the recommendation
│       └── optimization/               # MIP solver and greedy heuristic strategies
└── adapters/                   # concrete implementations of use_cases/ports/
    ├── json_data_loader.py
    ├── csv_result_writer.py
    ├── json_result_writer.py
    ├── directory_request_discovery.py
    └── json_solution_loader.py
tests/                  # mirrors src/ structure
data/                   # sample problem instances
```

Dependencies only point inward: `adapters/` imports from `use_cases/`, never the
reverse; `use_cases/solving/` internals (`OptimizationStrategy`,
`BaseTechnologySolver`) are separate from the public ports in
`use_cases/ports/` — they are pluggable strategies used only within the
solving pipeline itself, not something `adapters/` or `bootstrap.py` implement.

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

**What breaks if you skip this step?** `pytest` still works, since `pyproject.toml` adds `src` to the path just for pytest. But `python -m cli solve 1` will fail with an import error — `cli.py` imports `domain`, `use_cases`, etc. as top-level packages, and without the editable install Python has no way to find them under `src/` outside of pytest.

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
Each integration test drives the real CLI end-to-end against a pre-built "situation" (`tests/resources/<situation>/`) and checks two things: that the generated formulation (`model.lp`) matches a golden file, so an unintended change to the model is caught even though the formulation is otherwise only unit-tested in isolation; and situation-specific conditions on the outcome — e.g. the expected optimal calories, that an infeasible request exits non-zero and writes no solution, that tied optimal solutions still report the shared optimal total, or that a large instance correctly routes to the heuristic instead of the MIP solver.

### Run tests by layer
```bash
pytest tests/domain/                  # domain unit tests only
pytest tests/adapters/                # adapter tests only
pytest tests/use_cases/               # use case tests (excluding the solving pipeline)
pytest tests/use_cases/solving/       # solving pipeline: strategies, pre/postprocessing
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

### Solve a single knapsack optimization request
```bash
python -m cli solve 1  # solve request from data/1/data.json
python -m cli solve 2  # solve request from data/2/data.json
python -m cli solve 1 --format json  # write the result as JSON instead of CSV
```

### Solve every request in a folder
```bash
python -m cli solve-batch data  # solve every request subfolder under data/
```

### Check whether a candidate solution is feasible for a request
```bash
python -m cli evaluate 1 candidate_solution.json
```
where `candidate_solution.json` maps product name to candidate quantity:
```json
{ "apple": 4, "chocolate": 0 }
```

---

## How it works

This project follows a simplified **Clean Architecture** with three layers and
full dependency inversion — every collaborator is constructor-injected, and
`bootstrap.py` is the single place concrete objects get wired together:

1. **`domain/`** — Pure business logic (Product, Request, Recommendation) with no external dependencies.
2. **`use_cases/`** — Application rules, expressed as three independent use case classes (no shared base — their signatures genuinely differ):
   - **`SolveSingleRequest`** — load one request and run it through the solving pipeline.
   - **`SolveMultipleRequests`** — discover every request in a folder (via `BaseRequestDiscovery`) and solve each one with a composed `SolveSingleRequest`.
   - **`EvaluateSolutionForRequest`** — check whether a user-supplied candidate quantity dict is feasible for a request, with no solver involved: it builds a `Recommendation` and lets its existing budget/weight validation do the feasibility check.

   Abstract ports the use cases depend on (`BaseDataLoader`, `BaseResultWriter`, `BaseRequestDiscovery`, `BaseSolutionLoader`) live in `use_cases/ports/`.

   The solving pipeline itself lives in **`use_cases/solving/`** — an internal implementation detail of `SolveSingleRequest`, not a top-level architecture layer:
   - **`solving/orchestrator.py`** — Pipeline coordinator: runs preprocessing → picks a strategy → runs postprocessing.
   - **`solving/preprocessing/`** — Filters out products that can never be selected (individually infeasible).
   - **`solving/optimization/`** — Solver implementations:
     - **Greedy heuristic** — fast, approximate solution for large problems.
     - **MIP solver** — first assembles a **solver-agnostic model** (the formulation: variables, constraints, objective, in `model_abstraction/`, built from `components/`) using pure Python with no solver dependency. Only once that model exists is it handed to a technology-specific solver (`solvers/highs_solver.py`) to actually optimize. Because the formulation is a plain Python object, it can be unit-tested on its own — see `tests/use_cases/solving/optimization/mip/optimization/model_abstraction/` and `.../components/` — independent of whether HiGHS or any other solver is installed. `OptimizationStrategy` and `BaseTechnologySolver` are internal solving-strategy contracts, separate from the public ports in `use_cases/ports/`.
   - **`solving/postprocessing/`** — Refines the recommendation (e.g., sorts products by quantity).
3. **`adapters/`** — All I/O: concrete implementations of the `use_cases/ports/` interfaces (`JsonDataLoader`, `CsvResultWriter`/`JsonResultWriter`, `DirectoryRequestDiscovery`, `JsonSolutionLoader`).
4. **`bootstrap.py`** — The composition root: factory functions that assemble the full object graph, including resolving `Settings.solver_name` to a concrete solver.
5. **`cli.py`** — Parses arguments and dispatches to `bootstrap.py`; it never constructs a concrete adapter or use case itself.

---
