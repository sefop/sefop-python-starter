"""Semantic LP model comparer for linear integer programs.

This package provides order-agnostic comparison of two LP files at the
mathematical-model level, reporting precise differences down to individual
coefficients. Intended for use in integration tests to verify that
generated LP models match golden files without being sensitive to the
order in which variables, constraints, or objectives are written.
"""

from tests.helpers.lp_comparer.comparer import compare_lp
from tests.helpers.lp_comparer.models import LpDifference

__all__ = ["compare_lp", "LpDifference"]
