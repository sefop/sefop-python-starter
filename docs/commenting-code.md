# Commenting Code Guide

---

## 1. General Rules

Good comments capture what the code cannot express: *why* a design decision was made, what constraints
exist, and what non-obvious behavior a caller must understand. Restating the code in prose is not a
comment — it is noise. Never repeat in a comment the same words that make up the name of the thing
being described — if the name already says it, the comment adds nothing.

### Rule 1 — Comments explain WHY, not WHAT

Do not describe what the code does; describe why it does it. The reader can see the code. What they
cannot see is the reasoning, the constraints, or the alternatives that were rejected.

```python
# Bad — restates the code
total = price * quantity  # multiply price by quantity

# Good — explains the business rule
total = price * quantity  # gross total before tax; tax is applied at checkout
```

### Rule 2 — Keep comments close to the code they describe

Place comments immediately above or on the same line as the code they refer to. A comment separated
from its subject by blank lines or unrelated code will eventually become misleading.

### Rule 3 — Update comments when you update code

A stale comment is worse than no comment. When you change logic, update every comment that references
that logic in the same commit.

### Rule 4 — Use proper grammar and spelling

Comments are read by humans. Write complete sentences where practical. Use correct spelling and avoid
jargon that only a subset of the team would understand.

### Rule 5 — Do not comment out code

Delete dead code instead of commenting it out. Version control preserves history. Commented-out blocks
create uncertainty about whether the code is intentionally disabled or accidentally left behind.

```python
# Bad
# connection = create_legacy_connection(host, port)
connection = create_connection(host, port)

# Good — just delete the old line
connection = create_connection(host, port)
```

### Rule 6 — Avoid redundant comments

If a comment says exactly what the code says, remove it. Redundant comments add maintenance burden
without adding understanding.

```python
# Bad — the function name already says this
def get_total_price(items: list[Item]) -> float:
    """Gets the total price."""  # redundant
    ...

# Good — adds non-obvious information the name does not convey
def get_total_price(items: list[Item]) -> float:
    """Sum the unit prices of all items, excluding tax and discounts."""
    ...
```

### Rule 7 — Use TODO and FIXME tags

Mark incomplete work with `TODO` and known defects with `FIXME`. Always include a short explanation
of what remains to be done.

```python
# TODO: Replace linear scan with indexed lookup once the dataset exceeds 10k rows.
# FIXME: Division by zero when the denominator list is empty.
```

### Rule 8 — Prefer self-documenting code over comments

Before writing a comment, ask whether you can eliminate the need for it by choosing a better name,
extracting a helper function, or adding a type hint. Code that communicates its intent directly
is easier to maintain than code that relies on comments to explain itself.

```python
# Bad — comment compensates for a vague variable name
d = 86400  # number of seconds in a day

# Good — the name communicates the intent; no comment needed
SECONDS_PER_DAY = 86400
```

---

## 2. Module-Level Docstrings

Every module (`.py` file) that forms part of the public API or implements a significant responsibility
should begin with a module-level docstring. Place it as the very first statement in the file, before
imports.

A module docstring should state:
- What responsibility the module owns.
- How it fits into the broader system (one sentence is enough).

```python
"""Solvers for linear and mixed-integer optimization problems.

This module provides solver implementations that satisfy the
BaseTechnologySolver interface.
"""

import logging
from abc import ABC, abstractmethod

...
```

Do not include author names, dates, or version numbers in module docstrings. That information belongs
in version control.

---

## 3. Class Docstrings

A class docstring should give the reader a **strategic overview**: what responsibility the class owns,
how it fits into the broader design, and any non-obvious constraints a caller must respect. Do not
describe *how* the class works internally — algorithm choices and data structures are implementation
details that belong in inline comments, not in the class contract.

Ask yourself: *if I were using this class from the outside, what would I need to know?*

Use the `Attributes:` section (Google style) to document public attributes.

```python
# Bad — exposes implementation details (internal dictionary, threading)

class SessionCache:
    """Uses a dictionary to store session tokens, and a background thread
    that removes expired entries every 60 seconds.
    """
    ...

# Bad — too vague to be useful; could describe any class in the codebase

class SessionCache:
    """Manages sessions."""
    ...

# Good — explains the responsibility, lifecycle, and concurrency guarantee
# without mentioning any internal data structure or threading mechanism

class SessionCache:
    """Tracks active user sessions for the duration of a request-processing window.

    Sessions are valid from the moment they are registered until they expire
    or are explicitly invalidated. Expired sessions are removed automatically;
    callers do not need to clean up after themselves.

    This class is safe for concurrent use by multiple threads.

    Attributes:
        default_ttl_seconds: Time-to-live in seconds for newly registered
            sessions. Defaults to 3600.
    """

    default_ttl_seconds: int = 3600
    ...
```

When a class implements an abstract base class, the docstring should explain what *this specific class*
contributes — do not repeat what the base class already documents.

```python
# Bad — restates the interface contract without adding anything specific

class EmailNotificationSender(NotificationSender):
    """A NotificationSender that sends notifications."""
    ...

# Good — explains the scope and constraints of this particular implementation

class EmailNotificationSender(NotificationSender):
    """Delivers notifications via SMTP email.

    Each call to send() opens a new connection to the configured mail server.
    For high-frequency scenarios, prefer a batching sender implementation
    instead.
    """
    ...
```

---

## 4. Function and Method Docstrings

Document the *contract*, not the implementation. Explain what the function does, what the caller must
provide, what is returned, and any non-obvious preconditions or side effects. Use Google-style
sections: `Args:`, `Returns:`, and `Raises:`.

Always write docstrings for **public** functions and methods. For private helpers (`_` prefix) with
clear names and type hints, a docstring is optional — add one only when the behaviour is non-obvious.

```python
# Bad — implementation detail leaks into the contract

def get_cheapest_item(items: list[Item]) -> Item:
    """Iterates over the list of items, sorts them by price using
    the built-in sorted(), and returns the first one.
    """
    ...

# Good — states what, the precondition, and the return contract

def get_cheapest_item(items: list[Item]) -> Item:
    """Return the item with the lowest unit price among the given candidates.

    Args:
        items: Non-empty list of candidate items.

    Returns:
        The item with the smallest unit_price value.

    Raises:
        ValueError: If items is empty.
    """
    ...
```

For methods that override a base class method, only add a docstring if this implementation changes or
extends the documented contract. Otherwise, the base class docstring is inherited.

---

## 5. Type Hints as Documentation

Python 3.11 provides expressive type hints that serve as executable documentation. Well-chosen type
annotations reduce the need for comments by making function signatures self-describing.

Always annotate function parameters and return types. Use Python 3.11 union syntax (`X | Y`) instead
of `Optional[X]` or `Union[X, Y]`.

```python
# Without type hints — requires comments to explain the contract
def calculate_score(weights, values, default):
    """Calculate weighted score.

    Args:
        weights: List of float weights.
        values: List of float values.
        default: Default score if inputs are empty, or None.
    """
    ...

# With type hints — the signature documents the types; the docstring
# focuses on behaviour and business rules instead
def calculate_score(
    weights: list[float],
    values: list[float],
    default: float | None,
) -> float:
    """Return the dot product of weights and values.

    Falls back to default when both lists are empty. Raises ValueError
    when the lists have different lengths.
    """
    ...
```

Type hints do not replace docstrings. They document *types*; docstrings document *behaviour*,
*preconditions*, and *side effects*. Use both together.

---

## 6. Inline Comments

Use inline comments (`#`) to add precision that the code cannot express: units, boundary conditions,
non-obvious constraints, or the reason a seemingly wrong choice is actually correct.

Place inline comments on their own line above the code they describe. Use end-of-line comments only
for very short clarifications.

```python
# Bad — repeats what the code already says
remaining = end - now  # subtract now from end

# Good — explains the unit and inclusive/exclusive boundary
# Remaining session time in seconds. The 60-second grace period is
# subtracted before this check, so the boundary here is inclusive.
session_time_remaining_seconds = session_end_seconds - now_seconds
```

---

## 7. Constants and Variables

Document module-level constants with a preceding comment block that explains the purpose, valid value
range, unit, and the business rule it encodes. Always use `UPPER_CASE` names for constants.

```python
# Bad — no context; the reader must hunt for the source of this number
THRESHOLD = 72

# Good — states the unit, the business rule it encodes, and its origin
# Maximum look-ahead window in hours. Events scheduled beyond this
# horizon are excluded from processing.
# Source: configuration property "look_ahead_threshold_hours".
LOOK_AHEAD_THRESHOLD_HOURS = 72
```

For dataclass fields, document each field in the class docstring's `Attributes:` section rather than
with individual inline comments.

```python
@dataclass
class SolverConfig:
    """Configuration for the optimization solver.

    Attributes:
        max_iterations: Upper bound on solver iterations. Set to 0
            for unlimited iterations.
        time_limit_seconds: Wall-clock time limit in seconds. The solver
            returns the best solution found when this limit is reached.
    """

    max_iterations: int = 10_000
    time_limit_seconds: float = 300.0
```

---

## 8. SEFOP Architecture-Aware Comments

This section extends the general rules above with guidance specific to the SEFOP framework.
Every SEFOP template is a **teaching artifact** — it must be readable by a PhD student or
data scientist who knows optimization but may be new to software engineering patterns. Comments
in SEFOP templates carry an extra responsibility: they must explain *why the architecture is
designed this way*, not just what the code does.

### 8.1 — File-level role declaration

Every `.py` file in a SEFOP template must begin with a module docstring that describes its
role in the system and explains *why it exists*. This is the single most important comment
in the file — it orients a reader who opens the file cold.

```python
"""
ROLE: Abstract interface for optimization solvers.

WHY THIS EXISTS:
    This base class declares the contract any solver must fulfill: a ``solve(model)``
    method that returns a solution. By depending only on this base class, the
    optimization pipeline stays completely independent from third-party solver
    libraries. You can swap HiGHS for any future solver by adding a new subclass —
    no other code changes.

WHERE IMPLEMENTATIONS LIVE:
    Concrete solver implementations live in
    src/optimization/strategy/mip/optimization/solvers/.
"""
```

Use the following role labels consistently across all templates:

| Role | Directory | One-line purpose |
|------|-----------|-----------------|
| `Entity` | `src/domain/` | Pure data model, no dependencies, no solver imports. |
| `Value Object` | `src/domain/` | Immutable, self-validating descriptor of a quantity or concept. |
| `Abstract Base Class` | `src/services/` | Abstract interface that services depend on. |
| `Orchestrator` | `src/services/` | Orchestrates one user-facing operation end-to-end. |
| `Strategy` | `src/services/` or `src/optimization/` | Pluggable algorithm that produces a result from a request. |
| `Implementation` | `src/optimization/` | Concrete solver implementation for a specific technology. |

### 8.2 — Software-concept docstrings

When a class embodies a software engineering pattern that a data scientist may not recognize
(abstract base class, strategy pattern, dependency injection, frozen dataclass), the class
docstring must explain the pattern, not just the class's job. Write one paragraph for the
concept and one for this specific class.

```python
# Bad — assumes the reader knows what an abstract base class is for
class BaseTechnologySolver(ABC):
    """Abstract interface for optimization solvers."""

# Good — explains the pattern, then applies it to this class
class BaseTechnologySolver(ABC):
    """
    This is an abstract base class (ABC) — a contract pattern: it declares what methods must
    exist without providing their implementation. Think of it as a power socket: the interface
    (BaseTechnologySolver) defines the socket shape; any concrete implementation (e.g., HighsSolver)
    must conform to it.

    This base class declares that any solver implementation must provide a ``solve(model)`` method
    that returns a solution. The optimization pipeline calls ``solver.solve()`` without needing to
    know or care whether the underlying engine is HiGHS, Gurobi, or any other solver. Concrete
    solver implementations live in src/optimization/strategy/mip/optimization/solvers/.
    """

    @abstractmethod
    def solve(self, model: OptimizationModel) -> Solution:
        ...
```

Apply the same pattern to these recurring concepts:

- **Frozen dataclass** — explain immutability and why fail-fast validation matters.
- **Abstract Base Class (ABC)** — explain the contract metaphor before describing the class.
- **Strategy pattern** — explain that swappable algorithms share a common interface so the engine
  can choose between them without knowing their internals.
- **Orchestrator** — explain that it sequences one operation end-to-end and should contain no
  business logic of its own, only coordination.

### 8.3 — Teaching-level inline comments

In a SEFOP template, inline comments must be written for a reader who understands the
optimization problem but may not recognize the software engineering choice. Explain the
*why* in terms of the consequences of doing it differently.

```python
# Bad — states the obvious
self._solver = solver  # assign solver

# Bad — explains what but not why
self._solver = solver  # store the injected solver

# Good — explains the design consequence
# The solver is injected rather than instantiated here so that tests can
# pass a mock solver without a real HiGHS installation. This is Dependency
# Injection: the class declares what it needs; the caller decides what to provide.
self._solver = solver
```

For mathematical constructs in the optimization layer, always state the math alongside the
code so a reader can map between the Pyomo expression and the model formulation:

```python
# Constraint: ∑ w_i · x_i ≤ W
# Total weight of selected cargo must not exceed the aircraft's weight capacity W.
# Without this constraint the solver would load an unbounded amount of cargo,
# which is physically impossible.
model.weight_limit = Constraint(
    expr=sum(data.weight[i] * model.x[i] for i in model.I) <= data.capacity_weight
)
```

### 8.4 — What NOT to over-explain

Comment-heavy does not mean comment-everything. Even in a teaching template, avoid:

- Restating what a well-named function or variable already says (Rule 1 still applies).
- Explaining Python syntax (`for i in range(n)` does not need a comment).
- Repeating the same architecture explanation in every file — state it once in the layer
  declaration (Section 8.1) and refer the reader there if needed.

The test: *would a data scientist who just finished a Python tutorial need this comment?*
If yes, include it. If the answer is *only someone who has never seen a for-loop*, skip it.

---

## 9. References

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/) — covers inline comments,
  block comments, and naming conventions.
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/) — covers module, class, and
  function docstrings.
- [Google Python Style Guide — Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) —
  covers the `Args:`, `Returns:`, `Raises:` format used in this guide.

---