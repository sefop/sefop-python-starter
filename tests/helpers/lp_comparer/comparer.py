"""Semantic LP model comparer for linear integer programs.

This module provides order-agnostic comparison of two LP files at the
mathematical-model level, reporting precise differences down to individual
coefficients. Intended for use in integration tests to verify that
generated LP models match expected golden files without being sensitive to
the order in which variables, constraints, or objectives are written.
"""

from __future__ import annotations

import math
from pathlib import Path

from tests.helpers.lp_comparer.lp_parser import ConstraintInfo, ObjectiveInfo, ParsedLpModel, parse_lp_file
from tests.helpers.lp_comparer.models import LpDifference


def compare_lp(
    expected_path: Path,
    actual_path: Path,
    fail_fast: bool = False,
    tolerance: float = 1e-9,
) -> list[LpDifference]:
    """Compare two LP files semantically, returning a list of differences.

    Parses both files into a normalized mathematical representation and
    checks for differences at the model, variable, objective, and
    constraint level. All comparisons are order-agnostic.

    Args:
        expected_path: Path to the golden (expected) LP file.
        actual_path: Path to the freshly generated (actual) LP file.
        fail_fast: When ``True``, return after the first difference is
            found. When ``False`` (default) collect all differences.
        tolerance: Absolute tolerance used when comparing floating-point
            coefficients and RHS values. Defaults to ``1e-9``.

    Returns:
        A (possibly empty) list of :class:`~tests.helpers.lp_comparer.models.LpDifference`
        objects describing every semantic difference found. Returns an
        empty list when the two models are semantically equivalent.
    """
    expected = parse_lp_file(expected_path)
    actual = parse_lp_file(actual_path)

    diffs: list[LpDifference] = []

    # Stages run in dependency order: metadata first (cheapest check),
    # then variables (referenced by objectives and constraints), then
    # objectives, then constraints. In fail_fast mode the caller gets
    # the earliest, most fundamental difference.
    _check_model_metadata(expected, actual, diffs)
    if fail_fast and diffs:
        return diffs

    _check_variables(expected, actual, diffs, fail_fast)
    if fail_fast and diffs:
        return diffs

    _check_objectives(expected, actual, diffs, fail_fast, tolerance)
    if fail_fast and diffs:
        return diffs

    _check_constraints(expected, actual, diffs, fail_fast, tolerance)

    return diffs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_model_metadata(
    expected: ParsedLpModel,
    actual: ParsedLpModel,
    diffs: list[LpDifference],
) -> None:
    """Append model-level differences (name, sense) to *diffs*."""
    if expected.name != actual.name:
        diffs.append(
            LpDifference(
                category="model",
                diff_type="modified",
                name="",
                detail=f"Model name changed: expected '{expected.name}', got '{actual.name}'",
                expected=expected.name,
                actual=actual.name,
            )
        )

    if expected.sense != actual.sense:
        diffs.append(
            LpDifference(
                category="model",
                diff_type="modified",
                name="",
                detail=f"Optimization sense changed: expected '{expected.sense}', got '{actual.sense}'",
                expected=expected.sense,
                actual=actual.sense,
            )
        )


def _check_variables(
    expected: ParsedLpModel,
    actual: ParsedLpModel,
    diffs: list[LpDifference],
    fail_fast: bool,
) -> None:
    """Append variable-level differences to *diffs*."""
    expected_names = set(expected.variables)
    actual_names = set(actual.variables)

    # sorted() ensures deterministic diff output across runs
    for name in sorted(expected_names - actual_names):
        diffs.append(
            LpDifference(
                category="variable",
                diff_type="missing",
                name=name,
                detail=f"Variable '{name}' is in expected but missing from actual",
            )
        )
        if fail_fast:
            return

    for name in sorted(actual_names - expected_names):
        diffs.append(
            LpDifference(
                category="variable",
                diff_type="extra",
                name=name,
                detail=f"Variable '{name}' is in actual but not in expected",
            )
        )
        if fail_fast:
            return

    for name in sorted(expected_names & actual_names):
        exp_var = expected.variables[name]
        act_var = actual.variables[name]
        if exp_var.var_type != act_var.var_type:
            diffs.append(
                LpDifference(
                    category="variable",
                    diff_type="modified",
                    name=name,
                    detail=(f"Variable '{name}' type changed: expected '{exp_var.var_type}', got '{act_var.var_type}'"),
                    expected=exp_var.var_type,
                    actual=act_var.var_type,
                )
            )
            if fail_fast:
                return


def _check_objectives(
    expected: ParsedLpModel,
    actual: ParsedLpModel,
    diffs: list[LpDifference],
    fail_fast: bool,
    tolerance: float,
) -> None:
    """Append objective-level differences to *diffs*."""
    expected_names = set(expected.objectives)
    actual_names = set(actual.objectives)

    for name in sorted(expected_names - actual_names):
        diffs.append(
            LpDifference(
                category="objective",
                diff_type="missing",
                name=name,
                detail=f"Objective '{name}' is in expected but missing from actual",
            )
        )
        if fail_fast:
            return

    for name in sorted(actual_names - expected_names):
        diffs.append(
            LpDifference(
                category="objective",
                diff_type="extra",
                name=name,
                detail=f"Objective '{name}' is in actual but not in expected",
            )
        )
        if fail_fast:
            return

    for name in sorted(expected_names & actual_names):
        before = len(diffs)
        _check_objective_body(name, expected.objectives[name], actual.objectives[name], diffs, fail_fast, tolerance)
        if fail_fast and len(diffs) > before:
            return


def _check_objective_body(
    obj_name: str,
    expected: ObjectiveInfo,
    actual: ObjectiveInfo,
    diffs: list[LpDifference],
    fail_fast: bool,
    tolerance: float,
) -> None:
    """Append coefficient-level differences for a single objective."""
    exp_vars = set(expected.coefficients)
    act_vars = set(actual.coefficients)

    for var in sorted(exp_vars - act_vars):
        diffs.append(
            LpDifference(
                category="objective",
                diff_type="missing",
                name=obj_name,
                detail=f"Variable '{var}' is in objective '{obj_name}' in expected but missing from actual",
            )
        )
        if fail_fast:
            return

    for var in sorted(act_vars - exp_vars):
        diffs.append(
            LpDifference(
                category="objective",
                diff_type="extra",
                name=obj_name,
                detail=f"Variable '{var}' is in objective '{obj_name}' in actual but not in expected",
            )
        )
        if fail_fast:
            return

    for var in sorted(exp_vars & act_vars):
        exp_coef = expected.coefficients[var]
        act_coef = actual.coefficients[var]
        if not math.isclose(exp_coef, act_coef, abs_tol=tolerance):
            diffs.append(
                LpDifference(
                    category="objective",
                    diff_type="modified",
                    name=obj_name,
                    detail=(
                        f"Coefficient of '{var}' in objective '{obj_name}' differs: "
                        f"expected {exp_coef}, got {act_coef}"
                    ),
                    expected=exp_coef,
                    actual=act_coef,
                )
            )
            if fail_fast:
                return


def _check_constraints(
    expected: ParsedLpModel,
    actual: ParsedLpModel,
    diffs: list[LpDifference],
    fail_fast: bool,
    tolerance: float,
) -> None:
    """Append constraint-level differences to *diffs*."""
    expected_names = set(expected.constraints)
    actual_names = set(actual.constraints)

    for name in sorted(expected_names - actual_names):
        diffs.append(
            LpDifference(
                category="constraint",
                diff_type="missing",
                name=name,
                detail=f"Constraint '{name}' is in expected but missing from actual",
            )
        )
        if fail_fast:
            return

    for name in sorted(actual_names - expected_names):
        diffs.append(
            LpDifference(
                category="constraint",
                diff_type="extra",
                name=name,
                detail=f"Constraint '{name}' is in actual but not in expected",
            )
        )
        if fail_fast:
            return

    for name in sorted(expected_names & actual_names):
        before = len(diffs)
        _check_constraint_body(name, expected.constraints[name], actual.constraints[name], diffs, fail_fast, tolerance)
        if fail_fast and len(diffs) > before:
            return


def _check_constraint_body(
    con_name: str,
    expected: ConstraintInfo,
    actual: ConstraintInfo,
    diffs: list[LpDifference],
    fail_fast: bool,
    tolerance: float,
) -> None:
    """Append body-level differences for a single constraint."""
    if expected.operator != actual.operator:
        diffs.append(
            LpDifference(
                category="constraint",
                diff_type="modified",
                name=con_name,
                detail=f"Constraint '{con_name}' sense changed: expected '{expected.operator}', got '{actual.operator}'",
                expected=expected.operator,
                actual=actual.operator,
            )
        )
        if fail_fast:
            return

    if not math.isclose(expected.rhs, actual.rhs, abs_tol=tolerance):
        diffs.append(
            LpDifference(
                category="constraint",
                diff_type="modified",
                name=con_name,
                detail=f"Constraint '{con_name}' RHS changed: expected {expected.rhs}, got {actual.rhs}",
                expected=expected.rhs,
                actual=actual.rhs,
            )
        )
        if fail_fast:
            return

    exp_vars = set(expected.coefficients)
    act_vars = set(actual.coefficients)

    for var in sorted(exp_vars - act_vars):
        diffs.append(
            LpDifference(
                category="constraint",
                diff_type="missing",
                name=con_name,
                detail=f"Variable '{var}' is in constraint '{con_name}' in expected but missing from actual",
            )
        )
        if fail_fast:
            return

    for var in sorted(act_vars - exp_vars):
        diffs.append(
            LpDifference(
                category="constraint",
                diff_type="extra",
                name=con_name,
                detail=f"Variable '{var}' is in constraint '{con_name}' in actual but not in expected",
            )
        )
        if fail_fast:
            return

    for var in sorted(exp_vars & act_vars):
        exp_coef = expected.coefficients[var]
        act_coef = actual.coefficients[var]
        if not math.isclose(exp_coef, act_coef, abs_tol=tolerance):
            diffs.append(
                LpDifference(
                    category="constraint",
                    diff_type="modified",
                    name=con_name,
                    detail=(
                        f"Coefficient of '{var}' in constraint '{con_name}' differs: "
                        f"expected {exp_coef}, got {act_coef}"
                    ),
                    expected=exp_coef,
                    actual=act_coef,
                )
            )
            if fail_fast:
                return
