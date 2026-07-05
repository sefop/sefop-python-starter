import re

import pytest

from engine.optimization.mip.optimization.model_abstraction.linear_constraint import ConstraintSign, LinearConstraint
from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from engine.optimization.mip.optimization.model_abstraction.model_variable import ModelVariable, VarType
from engine.optimization.mip.optimization.model_abstraction.optimization_model import ObjectiveSense, OptimizationModel


def _model(variable_name: str = "x", constraint_name: str = "cap") -> OptimizationModel:
    objective = LinearExpression()
    objective.add(1.0, variable_name)

    lhs = LinearExpression()
    lhs.add(1.0, variable_name)

    return OptimizationModel(
        variables=[ModelVariable(name=variable_name, var_type=VarType.INTEGER)],
        constraints=[LinearConstraint(name=constraint_name, lhs=lhs, sign=ConstraintSign.LEQ, rhs=5.0)],
        objective_expression=objective,
        objective_sense=ObjectiveSense.MAXIMIZE,
    )


def test__optimization_model__given_variable_name_with_space__raises():
    # ACT / ASSERT
    with pytest.raises(ValueError, match=re.escape("select banana")):
        _model(variable_name="select banana")


def test__optimization_model__given_constraint_name_with_dot__raises():
    # ACT / ASSERT
    with pytest.raises(ValueError, match=re.escape("weight.limit")):
        _model(constraint_name="weight.limit")


def test__optimization_model__given_safe_names__constructs_successfully():
    # ACT
    model = _model(variable_name="select_banana", constraint_name="weight_limit")

    # ASSERT
    assert model.variables[0].name == "select_banana"
    assert model.constraints[0].name == "weight_limit"
