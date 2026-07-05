import pytest

from engine.optimization.mip.optimization.model_abstraction.linear_constraint import ConstraintSign, LinearConstraint
from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from engine.optimization.mip.optimization.model_abstraction.model_variable import ModelVariable, VarType
from engine.optimization.mip.optimization.model_abstraction.optimization_model import ObjectiveSense, OptimizationModel
from engine.optimization.mip.optimization.solvers.highs_solver import HighsSolver


@pytest.fixture
def tiny_model() -> OptimizationModel:
    """One integer variable x, maximized subject to x <= 5."""
    objective = LinearExpression()
    objective.add(1.0, "x")

    weight_expr = LinearExpression()
    weight_expr.add(1.0, "x")

    return OptimizationModel(
        variables=[ModelVariable(name="x", var_type=VarType.INTEGER, lower_bound=0.0, upper_bound=10.0)],
        constraints=[LinearConstraint(name="cap", lhs=weight_expr, sign=ConstraintSign.LEQ, rhs=5.0)],
        objective_expression=objective,
        objective_sense=ObjectiveSense.MAXIMIZE,
    )


def test__solve__given_output_dir__writes_model_lp_before_running(tiny_model, tmp_path):
    # ACT
    HighsSolver().solve(tiny_model, output_dir=tmp_path)

    # ASSERT
    assert (tmp_path / "model.lp").exists()


def test__solve__given_no_output_dir__writes_no_lp_file(tiny_model, tmp_path, monkeypatch):
    # ARRANGE — chdir into an empty tmp_path so any accidental write (e.g. to
    # a hardcoded relative path) would land here and be caught.
    monkeypatch.chdir(tmp_path)

    # ACT
    HighsSolver().solve(tiny_model)

    # ASSERT
    assert list(tmp_path.rglob("*.lp")) == []
